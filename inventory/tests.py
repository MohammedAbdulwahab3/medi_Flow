from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta

from authentication_app.models import User
from medicine.models import Medicine, MedicineBatch
from inventory.models import Inventory, PharmacyInventory, ReservationRequest, MedicineTransfer


class TransferFlowTest(TestCase):
	def setUp(self):
		# Create users
		self.manufacturer = User.objects.create_user(username='man', password='pass', role=User.ROLE_MANUFACTURER)
		self.pharmacist = User.objects.create_user(username='ph', password='pass', role=User.ROLE_PHARMACIST)

		# Create medicine and batch
		self.medicine = Medicine.objects.create(
			name='TestMed',
			generic_name='TM',
			strength='10mg',
			dosage_form='tablet',
			manufacturer=self.manufacturer,
		)
		self.batch = MedicineBatch.objects.create(
			medicine=self.medicine,
			batch_number='BATCH1',
			quantity=20,
			manufacturing_date=date.today() - timedelta(days=30),
			expiry_date=date.today() + timedelta(days=365),
			cost_price=1.00,
			selling_price=2.00,
		)

		# Create manufacturer inventory
		self.inv = Inventory.objects.create(batch=self.batch, current_stock=20, reserved_stock=0, minimum_stock_level=5)

	def test_request_accept_transfer_flow(self):
		client = Client()

		# Pharmacist logs in and creates a reservation request for 5 units
		client.login(username='ph', password='pass')
		resp = client.post(reverse('frontend:create_reservation_request'), {
			'manufacturer_id': self.manufacturer.id,
			'medicine_id': self.medicine.id,
			'quantity': 5,
		})
		# Request should be created
		req = ReservationRequest.objects.filter(pharmacy=self.pharmacist, manufacturer=self.manufacturer, medicine=self.medicine).first()
		self.assertIsNotNone(req, 'ReservationRequest was not created')

		# Manufacturer accepts the request (this should allocate and create transfer records)
		client.logout()
		client.login(username='man', password='pass')
		resp = client.get(reverse('frontend:manufacturer_respond_reservation', args=[req.id, 'accept']))

		# After acceptance, reservation status should be RESERVED
		req.refresh_from_db()
		self.assertEqual(req.status, ReservationRequest.STATUS_RESERVED)

		# Transfers should have been created and inventory decremented by allocated amount
		transfers = MedicineTransfer.objects.filter(from_user=self.manufacturer, to_user=self.pharmacist)
		self.assertTrue(transfers.exists(), 'No MedicineTransfer created')
		total_transferred = sum(t.quantity for t in transfers)
		self.assertGreaterEqual(total_transferred, 1)

		# Manufacturer inventory current_stock decreased accordingly (reserved earlier then decreased during transfer creation)
		self.inv.refresh_from_db()
		# initial was 20, after transfer it should be 20 - total_transferred
		self.assertEqual(self.inv.current_stock, 20 - total_transferred)

		# ReservationRequest note should contain transfer ids linking to created transfers
		req.refresh_from_db()
		self.assertIsNotNone(req.note)
		for t in transfers:
			self.assertIn(str(t.id), req.note)

		# Pharmacist accepts the transfers
		client.logout()
		client.login(username='ph', password='pass')
		for t in transfers:
			resp = client.post(reverse('frontend:accept_transfer', args=[t.id]))

		# PharmacyInventory should reflect the transfers (post_save/pre_save signals should apply quantities)
		p_inv = PharmacyInventory.objects.filter(pharmacist=self.pharmacist, batch=self.batch).first()
		self.assertIsNotNone(p_inv, 'PharmacyInventory was not created')
		self.assertEqual(p_inv.current_stock, total_transferred)

		# ReservationRequest should be marked transferred (if linked)
		req.refresh_from_db()
		# If transfers were linked to the request note, status should now be TRANSFERRED
		self.assertIn(req.status, [ReservationRequest.STATUS_RESERVED, ReservationRequest.STATUS_TRANSFERRED])
