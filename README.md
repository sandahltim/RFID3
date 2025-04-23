test_rfidpi/ RFID2
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── tabs.py
│   │   ├── tab1.py
│   │   ├── tab2.py
│   │   ├── tab4.py
│   │   ├── tab4.py
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
│   │   ├── tab1.html
│   │   ├── tab2.html
│   │   ├── tab3.html
│   │   ├── tab4.html
│   │   └── tab.html
├── static/
│   └── css/
│   │   └── style.css
│   └── js/
│   │   ├── tab.js
│   │   └── expand.js
│   └── lib/
│        ├── htmx/
│        │   └── htmx.min.js
│        └── bootstrap/
│            ├── bootstrap.min.css
│            └── bootstrap.bundle.min.js
├── scripts/
│   ├── migrate_db.sql
│   ├── update_rental_class_mappings.py
│   ├── migrate_hand_counted_items.sql
│   └── setup_mariadb.sh
├── run.py
├── config.py
└── logs/


git pull origin RFID2
> /home/tim/test_rfidpi/logs/gunicorn_error.log
> /home/tim/test_rfidpi/logs/gunicorn_access.log
> /home/tim/test_rfidpi/logs/app.log
> /home/tim/test_rfidpi/logs/sync.log
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service

cat /home/tim/test_rfidpi/logs/gunicorn_error.log
cat /home/tim/test_rfidpi/logs/app.log
cat /home/tim/test_rfidpi/logs/sync.log

source venv/bin/activate

So Resale tab.... It will actually be Resale/Rental Packs. It is part resale items, part packs of rental items that are too small to individually label and already come in packs of a certain quantity. The way we tell is the bin data on each item, if it is "resale" or "sold" it is a resale item. If bin is "pack" or "burst" then it is a rental pack. The kicker is we need a way to change the bin in the API for item master with a post/patch/put request I believe?

