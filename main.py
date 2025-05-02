from app import app
import routes
import admin_routes
import employer_routes
import jobseeker_routes
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
