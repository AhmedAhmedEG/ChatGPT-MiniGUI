# Preview
<p align="center">
<img src="https://user-images.githubusercontent.com/16827679/233804902-d949c984-e59a-422e-94d6-7f82fc119571.png">
</p>


# ChatGPT-MiniGUI
Simple GUI to interact with ChatGPT directly using an API key.

# How To Use
When you first lauch the app, a new file called "config.ini" will be created in the same directory as the app, edit it and paste your OpenAI API key in place of the phrase "APIKeyHere".

# How To Build From Code
1- Make a python virtual environment inside the project's folder with the name "venv" and run this command in it's shell: ```pip install pyside6 openai cx_Freeze```.

> **_NOTE:_** creating a virual environment is very important here becuase in the building process, all the packages in the python enviroment get packed inside the output folder, we can add exception per package and also write code to delete spacific files for us, but we need the minimum amount of packages in the environment.

2- Open the cmd and make sure the project's folder is your current working directory, then run Build.bat and it will handle the building and the size optimizing processes automatically.

> **_NOTE:_** The "Build.bat" file runs the "Builder.py" file in the virtual enviroment, "Builder.py" uses cx_Freeze package to build the application, it also exceludes unused base python libraries, and it also includes custom code that removes unused parts of pyside6 library that takes alot of extra space.
