Write-Host "Running seed data population script..."
Set-Location -Path "c:\Users\esrom\Desktop\Medi_Flow-Frontend-firstcomit"
py reset_and_seed_data.py
Write-Host "Script execution completed."
Pause