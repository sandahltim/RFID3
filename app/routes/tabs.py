from flask import Blueprint, redirect, url_for, jsonify

# Blueprint for routing tabs - DO NOT MODIFY BLUEPRINT NAME
# Added on 2025-04-21 to handle tab routing
tabs_bp = Blueprint('tabs', __name__)

@tabs_bp.route('/tab/<int:tab_num>')
def tab_view(tab_num):
    # Route to redirect to the appropriate tab view based on tab number
    # Updated on 2025-04-21 to include Tab 4 (Laundry)
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_view'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_view'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_view'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_view'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/categories')
def tab_categories(tab_num):
    # Route to redirect to the appropriate tab categories endpoint
    # Updated on 2025-04-21 to include Tab 4 (Laundry)
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_categories'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_categories'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_categories'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_categories'))
    else:
        return '<tr><td colspan="6">Tab not implemented</td></tr>'

@tabs_bp.route('/tab/<int:tab_num>/subcat_data')
def subcat_data(tab_num):
    # Route to redirect to the appropriate tab subcategory data endpoint
    # Updated on 2025-04-21 to include Tab 4 (Laundry)
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_subcat_data'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_subcat_data'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_subcat_data'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_subcat_data'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/common_names')
def common_names(tab_num):
    # Route to redirect to the appropriate tab common names endpoint
    # Updated on 2025-04-21 to include Tab 4 (Laundry)
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_common_names'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_common_names'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_common_names'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_common_names'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404

@tabs_bp.route('/tab/<int:tab_num>/data')
def tab_data(tab_num):
    # Route to redirect to the appropriate tab data endpoint
    # Updated on 2025-04-21 to include Tab 4 (Laundry)
    if tab_num == 1:
        return redirect(url_for('tab1.tab1_data'))
    elif tab_num == 2:
        return redirect(url_for('tab2.tab2_data'))
    elif tab_num == 3:
        return redirect(url_for('tab3.tab3_data'))
    elif tab_num == 4:
        return redirect(url_for('tab4.tab4_data'))
    else:
        return jsonify({'error': 'Tab not implemented'}), 404