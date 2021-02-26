# Demo Web App

This folder includes minimal example of how to deploy the `TextLabelingTool` component as web application using Flask. This app depends on `flask` and `flask_socketio` libraries. Make sure install them by running:

```
pip install -r requirements.txt
```

You should also have TextLabelingTool installed either from PyPI or from this local repository. To install the local version, you can build and install the package as follows:
```sh
# move to JS source code folder and build it
cd TextLabelingTool/TextLabeling
npm install
npm run build
# move to the python package folder (where setup.py is located)
cd TextLabelingTool/
# build and install the python package
pip install -e .
```

Finally, run the following command to run this web app:
```sh
# run the Flask web app
cd TextLabelingTool/webapp
python3 app.py
```

Alternatively, to run a development version (with auto-reload after code changes), you can run:
```
FLASK_APP=app.py FLASK_ENV=development flask run
```

The app will be available at address http://127.0.0.1:5000/.