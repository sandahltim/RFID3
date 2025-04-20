# -rfidpi
test_rfidpi/ RFID2
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── tabs.py
│   │   ├── categories.py
│   │   └── health.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   └── scheduler.py
│   ├── models/
│   │   └── db_models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── categories.html
│   │   ├── home.html
│   │   └── tab.html
├── static/
│   └── css/
│   │   └── style.css
│   └── js/
│   │   └── tab.js
│   └── lib/
├── scripts/
│   ├── migrate_db.sql
│   └── setup_mariadb.sh
├── run.py
├── config.py
└── logs/
