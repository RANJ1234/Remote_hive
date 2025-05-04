from admin import create_admin_app

if __name__ == '__main__':
    app = create_admin_app()
    app.run(debug=True, port=5001)
