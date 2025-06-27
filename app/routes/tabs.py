# app/routes/tabs.py
# Version: 2025-06-27-v5
from flask import Blueprint, redirect, url_for, jsonify, current_app, render_template
from datetime import datetime
import logging
import sys

# Configure logging
logger = logging.getLogger('tabs')
logger.setLevel(logging.INFO)
logger.handlers = []  # Clear existing handlers
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

tabs_bp = Blueprint('tabs', __name__)

# Version marker
logger.info("Deployed tabs.py version: 2025-06-27-v5 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@tabs_bp.route('/tab/<int:tab_num>')
def tab_view(tab_num):
    logger.debug(f"Routing request for /tab/{tab_num} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if tab_num == 1:
        logger.debug("Redirecting to tab1.tab1_view at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return redirect(url_for('tab1.tab1_view'))
    elif tab_num == 2:
        logger.debug("Redirecting to tab2.tab2_view at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return redirect(url_for('tab2.tab2_view'))
    elif tab_num == 3:
        logger.debug("Redirecting to tab3.tab3_view at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return redirect(url_for('tab3.tab3_view'))
    elif tab_num == 4:
        logger.debug("Redirecting to tab4.tab4_view at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return redirect(url_for('tab4.tab4_view'))
    elif tab_num == 5:
        logger.debug("Redirecting to tab5.tab5_view at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return redirect(url_for('tab5.tab5_view'))
    else:
        logger.warning(f"Tab {tab_num} not implemented at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return render_template('common.html', tab_num=tab_num)

@tabs_bp.route('/tab/<int:tab_num>/categories')
def tab_categories(tab_num):
    logger.debug(f"Routing categories request for /tab/{tab_num} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_categories'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_categories'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_categories'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_categories'))
    elif tab_num == 5:
        return redirect(url_for('tab5.tab5_categories'))
    else:
        return '<tr><td colspan="6">Tab not implemented</td></tr>'

@tabs_bp.route('/tab/<int:tab_num>/subcat_data')
def subcat_data(tab_num):
    logger.debug(f"Routing subcat_data request for /tab/{tab_num} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_subcat_data'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_subcat_data'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_subcat_data'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_subcat_data'))
    elif tab_num == 5:
        return redirect(url_for('tab5.tab5_subcat_data'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/common_names')
def common_names(tab_num):
    logger.debug(f"Routing common_names request for /tab/{tab_num} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_common_names'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_common_names'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_common_names'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_common_names'))
    elif tab_num == 5:
        return redirect(url_for('tab5.tab5_common_names'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/data')
def tab_data(tab_num):
    logger.debug(f"Routing data request for /tab/{tab_num} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_data'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_data'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_data'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_data'))
    elif tab_num == 5:
        return redirect(url_for('tab5.tab5_data'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404