from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///module_data.db'
db = SQLAlchemy(app)

# Model for the Module Data
class ModuleData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    module_name = db.Column(db.String(100))
    module_group = db.Column(db.String(10))
    compulsory_elective = db.Column(db.String(10))
    semester = db.Column(db.Integer)
    acquired_points = db.Column(db.Integer)

    def __init__(self, date, module_name, module_group, compulsory_elective, semester, acquired_points):
        self.date = date
        self.module_name = module_name
        self.module_group = module_group
        self.compulsory_elective = compulsory_elective
        self.semester = semester
        self.acquired_points = acquired_points

# Data structure to store the module groups
module_groups = {
    'BWL': {'compulsory_points': 24, 'electives_required': 8, 'major_points': 20},
    'SQL': {'compulsory_points': 24, 'electives_required': 8, 'major_points': 20},
    'SLM': {'compulsory_points': 24, 'electives_required': 8, 'major_points': 20},
    'SOZ': {'compulsory_points': 34, 'electives_required': 4, 'major_points': 20},
    'BT': {'compulsory_points': 22, 'electives_required': 0, 'major_points': 20}
}

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/data', methods=['GET', 'POST'])
def module_form():
    if request.method == 'POST':
        entered_data = ModuleData(
            date=request.form['date'],
            module_name=request.form['module_name'],
            module_group=request.form['module_group'],
            compulsory_elective=request.form['compulsory_elective'],
            semester=int(request.form['semester']),
            acquired_points=int(request.form['acquired_points'])
        )

        db.session.add(entered_data)
        db.session.commit()

    latest_data = ModuleData.query.order_by(ModuleData.id.desc()).all()

    # Calculate acquired points for PF and WPF separately
    pf_acquired_points = sum(entry.acquired_points for entry in latest_data if entry.compulsory_elective == 'PF')
    wpf_acquired_points = sum(entry.acquired_points for entry in latest_data if entry.compulsory_elective == 'WPF')
    total_points = pf_acquired_points + wpf_acquired_points

    module_groups = ['BWL', 'SQL', 'SLM', 'SOZ', 'BT']
    module_group_acquired_points = {}

    for module_group in module_groups:
        module_group_data = ModuleData.query.filter_by(module_group=module_group).all()
        module_group_pf_points = sum(entry.acquired_points for entry in module_group_data if entry.compulsory_elective == 'PF')
        module_group_wpf_points = sum(entry.acquired_points for entry in module_group_data if entry.compulsory_elective == 'WPF')
        module_group_total_points = module_group_pf_points + module_group_wpf_points

        module_group_acquired_points[module_group] = {
            'pf_acquired_points': module_group_pf_points,
            'wpf_acquired_points': module_group_wpf_points,
            'total_points': module_group_total_points
        }
    passing_conditions = {
        'BWL': {'compulsory': 24, 'electives': 8},
        'SQL': {'compulsory': 24, 'electives': 8},
        'SLM': {'compulsory': 24, 'electives': 8},
        'SOZ': {'compulsory': 34, 'electives': 4},
        'BT': {'compulsory': 22}
    }

    passing_status = {}

    for module_group, conditions in passing_conditions.items():
        compulsory_points = conditions.get('compulsory', 0)
        electives_points = conditions.get('electives', 0)

        module_group_points = module_group_acquired_points.get(module_group, {}).get('total_points', 0)
        remaining_compulsory = max(0, compulsory_points - module_group_points)
        remaining_electives = max(0, electives_points - max(0, module_group_points - compulsory_points))
       
        if module_group_points >= compulsory_points:
            if electives_points == 0 or module_group_points >= compulsory_points + electives_points:
                passing_status[module_group] = 'Pass'
            else:
                passing_status[module_group] = 'Fail (Insufficient Elective Points)'
        else:
            passing_status[module_group] = 'Fail (Insufficient Compulsory Points)'
        # Add the following lines
        passing_status[module_group] += f" ({remaining_compulsory} Compulsory Remaining, {remaining_electives} Electives Remaining)"
    return render_template('view.html', latest_data=latest_data, pf_acquired_points=pf_acquired_points, wpf_acquired_points=wpf_acquired_points, total_points=total_points, module_group_acquired_points=module_group_acquired_points, passing_status=passing_status)


    return render_template('view.html', latest_data=latest_data, pf_acquired_points=pf_acquired_points, wpf_acquired_points=wpf_acquired_points, total_points=total_points, module_group_acquired_points=module_group_acquired_points)

@app.route('/view')
def view():
    # Retrieve all module data from the database
    all_data = ModuleData.query.all()

    return render_template('view.html', data=all_data)

@app.route('/delete-database', methods=['GET'])
def delete_database():
    # Delete all records from the ModuleData table
    db.session.query(ModuleData).delete()

    # Commit the changes to the database
    db.session.commit()

    # Clear any remaining objects in the session
    db.session.expunge_all()
    db.session.close()

    return "Database cleared successfully."


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
