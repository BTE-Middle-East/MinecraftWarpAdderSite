from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from waitress import serve

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://username:password@host:port/database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model for storing the file data
class FileData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)
    file_content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<FileData {self.name}>'

# Route for the form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        coordinates = request.form['coordinates']

        # Split the coordinates into x, y, z
        try:
            x, y, z = map(float, coordinates.split(','))
        except ValueError:
            return "Invalid coordinates format. Please use 'x, y, z'."

        # Template with default values
        file_content = f"""world: 1c617a1b-94f2-4311-9ae2-c4102bf1e96f
world-name: world
x: {x}
y: {y}
z: {z}
yaw: 0
pitch: 0
name: {name}
lastowner: ea0064bf-04dc-419e-8a0d-311c9a2b7a87
"""

        # Save the data in the database
        new_file = FileData(name=name, x=x, y=y, z=z, file_content=file_content)
        db.session.add(new_file)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('index.html')

# Run the app using Waitress
if __name__ == '__main__':
    # Initialize the database tables
    with app.app_context():
        db.create_all()

    serve(app, host='0.0.0.0', port=8080)
