from flask import Blueprint, redirect, url_for, jsonify

# Blueprint for routing tabs - DO NOT MODIFY BLUEPRINT NAME
# Added on 2025-04-21 to handle tab routing
tabs_bp = Blueprint('tabs', __name__)

@tabs_bp.route('/tab/<int:tab_num>')
def tab_view(tab_num):
    # Route to redirect to the appropriate tab view based on tab number
    # Updated on 2025-04-23 to include Tab 5 (Resale/Rental Packs)
    current_app.logger.info(f"Routing request for /tab/{tab_num}")
    if tab_num == 1:
        current_app.logger.info("Redirecting to tab1.tab1_view")
        return redirect(url_for('tab1.tab1_view'))
    elif tab_num == 2:
        current_app.logger.info("Redirecting to tab2.tab2_view")
        return redirect(url_for('tab2.tab2_view'))
    elif tab_num == 3:
        current_app.logger.info("Redirecting to tab3.tab3_view")
        return redirect(url_for('tab3.tab3_view'))
    elif tab_num == 4:
        current_app.logger.info("Redirecting to tab4.tab4_view")
        return redirect(url_for('tab4.tab4_view'))
    elif tab_num == 5:
        current_app.logger.info("Redirecting to tab5.tab5_view")
        return redirect(url_for('tab5.tab5_view'))
    else:
        current_app.logger.warning(f"Tab {tab_num} not implemented")
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/categories')
def tab_categories(tab_num):
    # Route to redirect to the appropriate tab categories endpoint
    # Updated on 2025-04-23 to include Tab 5 (Resale/Rental Packs)
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
    # Route to redirect to the appropriate tab subcategory data endpoint
    # Updated on 2025-04-23 to include Tab 5 (Resale/Rental Packs)
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
    # Route to redirect to the appropriate tab common names endpoint
    # Updated on 2025-04-23 to include Tab 5 (Resale/Rental Packs)
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
    # Route to redirect to the appropriate tab data endpoint
    # Updated on 2025-04-23 to include Tab 5 (Resale/Rental Packs)
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