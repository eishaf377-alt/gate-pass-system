import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app import app, db, User, GatePass
from werkzeug.security import generate_password_hash

def run_tests():
    print("Setting up test database...")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        
        # Test 1: User Registration
        print("Test 1: Creating Users...")
        student = User(username='student1', password='password', role='student')
        admin = User(username='admin1', password='password', role='admin')
        db.session.add(student)
        db.session.add(admin)
        db.session.commit()
        
        assert User.query.count() == 2
        print("PASS: Users created.")

        # Test 2: Create Gate Pass
        print("Test 2: creating Gate Pass Request...")
        from datetime import datetime
        pass_request = GatePass(
            user_id=student.id,
            reason="Going home",
            out_time=datetime.now(),
            in_time=datetime.now()
        )
        db.session.add(pass_request)
        db.session.commit()
        
        assert GatePass.query.count() == 1
        assert GatePass.query.first().status == 'Pending'
        print("PASS: Gate Pass created.")

        # Test 3: Admin Approval
        print("Test 3: Admin Approval...")
        gp = GatePass.query.first()
        gp.status = 'Approved'
        db.session.commit()
        
        assert GatePass.query.first().status == 'Approved'
        print("PASS: Gate Pass approved.")

        print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"FAILED: {e}")
        exit(1)
