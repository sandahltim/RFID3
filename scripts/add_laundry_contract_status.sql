-- Migration script to add laundry contract status tracking
-- Added for enhanced laundry contract management with finalization and return tracking

CREATE TABLE IF NOT EXISTS laundry_contract_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'finalized', 'returned'
    finalized_date DATETIME NULL,
    finalized_by VARCHAR(100) NULL,
    returned_date DATETIME NULL,
    returned_by VARCHAR(100) NULL,
    pickup_date DATETIME NULL,
    pickup_by VARCHAR(100) NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract_number (contract_number),
    INDEX idx_status (status),
    INDEX idx_finalized_date (finalized_date)
);

-- Installation instructions for auto-finalization (runs Wed/Fri 7am same as snapshots):
-- 1. Make the script executable:
--    chmod +x /home/tim/RFID3/scripts/auto_finalize_laundry.py
-- 2. Install systemd service and timer:
--    sudo cp /home/tim/RFID3/scripts/laundry-auto-finalize.service /etc/systemd/system/
--    sudo cp /home/tim/RFID3/scripts/laundry-auto-finalize.timer /etc/systemd/system/
--    sudo systemctl daemon-reload
--    sudo systemctl enable laundry-auto-finalize.timer
--    sudo systemctl start laundry-auto-finalize.timer
-- 3. Check timer status:
--    sudo systemctl status laundry-auto-finalize.timer
--    sudo systemctl list-timers laundry-auto-finalize.timer