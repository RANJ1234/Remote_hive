# Remote Hive

A job board platform for remote work opportunities.

## Overview

Remote Hive is a web application that connects remote job seekers with employers offering remote work opportunities. The platform allows employers to post job listings and job seekers to search and apply for positions.

## Features

- User authentication (job seekers, employers, admins)
- Job posting and management
- Company profiles
- Job search with filters
- Job applications
- Company reviews
- Admin dashboard

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MongoDB with MongoEngine ODM
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login

## Prerequisites

- Python 3.11 or higher
- MongoDB (local installation or MongoDB Atlas)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/remote-hive.git
   cd remote-hive
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

   Or use the setup script:
   ```
   python setup_and_run.py
   ```

## Configuration

1. MongoDB Connection:
   - The application will try to connect to a local MongoDB instance by default
   - To use MongoDB Atlas or a different connection string, set the `MONGODB_URI` environment variable:
     ```
     # Windows
     set MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/remotehive
     
     # macOS/Linux
     export MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/remotehive
     ```

2. Secret Key:
   - For production, set a secure secret key:
     ```
     # Windows
     set SESSION_SECRET=your-secure-secret-key
     
     # macOS/Linux
     export SESSION_SECRET=your-secure-secret-key
     ```

## Running the Application

1. Make sure MongoDB is running

2. Seed the database with initial data:
   ```
   python seed_database.py
   ```

3. Start the application:
   ```
   python main.py
   ```

   Or use the setup script to do all steps at once:
   ```
   python setup_and_run.py
   ```

4. Access the application at http://localhost:5000

## Default Users

After seeding the database, the following users will be available:

- **Admin**:
  - Email: admin@remotehive.com
  - Password: admin123

- **Employer**:
  - Email: employer@example.com
  - Password: password123

- **Job Seeker**:
  - Email: jobseeker@example.com
  - Password: password123

## License

This project is licensed under the MIT License - see the LICENSE file for details.
