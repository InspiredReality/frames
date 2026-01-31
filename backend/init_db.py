#!/usr/bin/env python
"""Initialize database tables for production."""
import sys
from app import create_app, db

def init_database():
    """Create all database tables."""
    app = create_app()

    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully!")

            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")

            return True
        except Exception as e:
            print(f"✗ Error creating database tables: {e}", file=sys.stderr)
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
