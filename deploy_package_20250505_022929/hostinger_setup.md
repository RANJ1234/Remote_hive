# Deploying Remote Hive to Hostinger

This guide provides instructions for deploying the Remote Hive application to Hostinger shared hosting.

## Prerequisites

1. A Hostinger hosting account
2. FTP credentials (provided in your Hostinger control panel)
3. A MongoDB database (either hosted externally or set up through Hostinger)

## Deployment Steps

### 1. Prepare Your Application

Before deploying, make sure your application is ready for production:

- Update your `.env` file with production settings
- Ensure all dependencies are listed in `requirements.txt`
- Test your application locally

### 2. Deploy Using the Script

The `deploy_to_hostinger.py` script automates the deployment process:

```bash
python deploy_to_hostinger.py
```

This script will:
- Create a deployment package with production-ready files
- Connect to your Hostinger FTP server
- Upload the files to the `public_html` directory
- Set up necessary configuration files

### 3. Configure Python Environment on Hostinger

Hostinger shared hosting supports Python applications through Passenger WSGI. The deployment script creates a `passenger_wsgi.py` file that serves as the entry point for your application.

If you need to install additional Python packages, you can do so using SSH access:

1. Log in to your Hostinger account
2. Enable SSH access in the control panel
3. Connect via SSH
4. Create a virtual environment and install dependencies:

```bash
cd ~/public_html
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure MongoDB Connection

Make sure your MongoDB connection string is correctly set in the `.env` file on the server:

```
MONGODB_URI=mongodb+srv://username:password@your-mongodb-host/remotehive
```

If you're using an external MongoDB provider like MongoDB Atlas, make sure to:
1. Whitelist your Hostinger server's IP address in the MongoDB Atlas dashboard
2. Use a strong password for your MongoDB user
3. Enable TLS/SSL for the connection

### 5. Set Up Domain and SSL

In your Hostinger control panel:

1. Configure your domain to point to your hosting account
2. Enable SSL/TLS for your domain
3. Make sure your application is accessible via HTTPS

### 6. Troubleshooting

If you encounter issues with your deployment:

1. Check the error logs in your Hostinger control panel
2. Verify that your `.env` file contains the correct configuration
3. Make sure your MongoDB connection is working
4. Check that all required Python packages are installed

## Additional Resources

- [Hostinger Python Hosting Documentation](https://www.hostinger.com/tutorials/how-to-host-python-website)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/3.1.x/deploying/)
