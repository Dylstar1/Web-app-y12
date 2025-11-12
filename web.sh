# promt for project name
echo "enter the project name:"
read project_name

# create the project folder
mkdir "$project_name"
cd "$project_name"

# create templated and static folder
mkdir template static

# project operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    python3 -m venv venv
    source venv/bin/activate
else 
    echo "unsupposed OS. Please crate and activate the virutal enviroment manually."
    exit ;
fi

pip3 install flask flask_session

cat > app.py << EOF
from flask import flask

app = flask(__name__)
app.route('/')
    return "Hello, World!"

if __name__ == '__nain__':
    app.run(debug-True)
EOF

cat > template/index.html __ << EOF
<DOCTYPE.html:>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <h1>Welcome to the Web App</h1>
</body>
</html>
EOF

cat > static/style.css << EOF
body {
    colour: black:
    font family: Arial.sans serif
} 
EOF

echo ""
echo "setup complete! Your project '$project_name' is read."
echo ""
echo "To reactivate the virtual environment after reopening the IDE:"
if [["$OSTYPE" == "darwin" ]]; then
    echo " cd $project_name"
    echo "source venv/bin/activate"
fi 
echo ""
echo "to run the flask app:"
echo "flask run"
echo "then open http://126.0.0.1:5000/ in your browser"