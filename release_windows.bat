echo off
cls

rem ************************************************************************************
rem *********************  ---> New batch file starts here <---  ***********************
rem **                                                                                **
rem **  This batch will compile automated via command line an executable              **
rem **  Pronterface file for Windows 10.                                              **
rem **                                                                                **
rem **  Steps that are automated:                                                     **
rem **                                                                                **
rem **  1. clean up previous compilations (directory .\dist)                          **
rem **  2. check for virtual environment called v3 and generate it, if                **
rem **     not available (start from scratch)                                         **
rem **  3. install all needed additional modules via pip                              **
rem **  4. check for outdated modules that need to be updated and                     **
rem **     update them                                                                **
rem **  5. Check if virtual environment needs an update and do it                     **
rem **  6. check for existing variants of gcoder_line.cp??-win_amd??.pyd              **
rem **     and delete them (to prevent errors and incompatibilities)                  **
rem **  7. compile Pronterface.exe                                                    **
rem **  8. copy localization files to .\dist                                          **
rem **  9. go to directory .\dist, list files and ends the activity                   **
rem **                                                                                **
rem **  Steps, you need to do manually before running this batch:                     **
rem **                                                                                **
rem **  1. install python 3.7.9                                                       **
rem **     https://www.python.org/downloads/release/python-379/                       **
rem **     In case you use an other Python version, check line 73 and adjust          **
rem **     the parameter accordingly to build your virtual environment.               **
rem **  2. install C-compiler environment                                             **
rem **     https://wiki.python.org/moin/WindowsCompilers                              **
rem **  3. check for latest repository updates at:                                    **
rem **     http://github.com/kliment/Printrun.git                                     **
rem **  4. Projector needs GTK+ for Windows Runtime Environment installed.            **
rem **     There are different compilations, depending on the installed               **
rem **     Windows Version, available. You can find a striped version of GTK3         **
rem **     with all needed DLL binary files in directory PrintrunGTK. Please run      **
rem **     following git commands before you run this batch in case you don't find    **
rem **     this directory in your repository:                                         **
rem **       git checkout master                                                      ** 
rem **       git submodule add https://github.com/DivingDuck/PrintrunGTK3             **
rem **       git submodule update --init --recursive                                  **
rem **     You can find a listing of all used DLL's in file VERSION as reference and  **
rem **     further informations about the linked submodule here:                      **
rem **     https://github.com/DivingDuck/PrintrunGTK3                                 **
rem **                                                                                **
rem **     Follow the instructions at section 'Collect all data for build' below      **
rem **                                                                                **
rem **  Author: DivingDuck, 2021-03-20, Status: working                               **
rem **                                                                                **
rem ************************************************************************************
rem ************************************************************************************

echo **************************************************
echo ****** Delete files and directory of .\dist ******
echo **************************************************
if exist dist (
   DEL /F/Q/S dist > NUL
   RMDIR /Q/S dist
   )
echo *********************************************
echo ****** Activate virtual environment v3 ******
echo *********************************************
if exist v3 (
   call v3\Scripts\activate
   ) else (

   echo **********************************************************************
   echo ****** No virtual environment named v3 available                ******
   echo ****** Will create first a new virtual environment with name v3 ******
   echo **********************************************************************
   py -3.7 -m venv v3

   echo *********************************************
   echo ****** Activate virtual environment v3 ******
   echo *********************************************
   call v3\Scripts\activate

   pip install --upgrade pip
   pip install --upgrade setuptools

   pip install wheel
   
   echo **********************************
   echo ****** install requirements ******
   echo **********************************
   pip install cython
   pip install -r requirements.txt
   
   echo ***********************
   echo ****** additions ******
   echo ***********************
   pip install simplejson
   pip install pyinstaller
   pip install pypiwin32
   pip install polygon3
   )

echo ********************************************
echo ****** upgrade virtual environment v3 ******
echo ********************************************
pip install --upgrade virtualenv
 
echo ****************************************************
echo ****** check for and update outdated modules  ******
echo ****************************************************
for /F "skip=2 delims= " %%i in ('pip list --outdated') do pip install --upgrade %%i

echo ***************************************************************
echo ****** Bug on wxPython 4.1.x workaround for Python 3.8.x ******
echo ***************************************************************
rem wxPython 4.1.1 cause a crash under Windows 10, Issue #1170
rem Relevant in combination with Python 3.8.x. Further information:
rem https://discuss.wxpython.org/t/wxpython4-1-1-python3-8-locale-wxassertionerror/35168
rem  pip uninstall wxPython
rem  pip install wxPython>=4.0,<4.1
rem Using the latest development version seems to correct the problem with wxPython.
rem The workaround below need to be check again as soon as there is a 
rem new version >4.1.1 available.
pip install -U --pre -f https://wxpython.org/Phoenix/snapshot-builds/ wxPython


echo ******************************************************************
echo ****** Compile G-Code parser gcoder_line.cp37-win_amd64.pyd ******
echo ******************************************************************
rem For safety reasons delete existing version first to prevent errors
if exist printrun\gcoder_line.cp??-win_amd??.pyd (
   del printrun\gcoder_line.cp??-win_amd??.pyd
   echo ********************************************************************************
   echo ****** found versions of printrun\gcoder_line.cp??-win_amd??.pyd, deleted ******
   echo ********************************************************************************
   )
python setup.py build_ext --inplace

echo ****************************************
echo ****** Collect all data for build ******
echo ****************************************

rem **** Select witch version you want to build: ****
rem The Pronterface Projector feature need some external DLL binaries from the GTK3.
rem You can build Pronterface with or w/o these binaries. In addition you need
rem different binaries depending if you build a Windows 10 x32 or x64 version.
rem Remove 'rem' before pyi-makespec for the build of your choice and add 'rem' for
rem for all other versions. you can't bundle x32 and x46 into the same Pronterface binary file.
rem Only one active version is allowed. 

rem **** Default setup: Version 3, GTK3 bundle included for Windows 10 x64 bit.  ****

rem Version 1: With external GTK3 or w/o GTK3 support: 
rem Choose this pyi-makespec in case you don't have the GTK3 Toolkit files, or want them stay separately
rem or don't want to bundle these within Pronterface.exe. You can install them separately and 
rem set the path location via Windows system environment variable (like Path=c:\GTK3\bin). 
rem pyi-makespec -F --add-data VERSION;cairocffi --add-data VERSION;cairosvg --add-data images/*;images --add-data *.png;. --add-data *.ico;. -w -i pronterface.ico pronterface.py

rem Version 2: GTK3 included in Pronterface (Windows10 x32 only):
rem Choose this pyi-makespec in case you want to include the GTK3 Toolkit files for Windows10 x32 only
rem pyi-makespec -F --add-binary PrintrunGTK3/GTK3Windows10-32/*.dll;. --add-data VERSION;cairocffi --add-data VERSION;cairosvg --add-data images/*;images --add-data *.png;. --add-data *.ico;. -w -i pronterface.ico pronterface.py

rem Version 3: GTK3 included in Pronterface (Windows10 x64 only):
rem Choose this pyi-makespec in case you want to include the GTK3 Toolkit files for Windows10 x64 only
pyi-makespec -F --add-binary PrintrunGTK3/GTK3Windows10-64/*.dll;. --add-data VERSION;cairocffi --add-data VERSION;cairosvg --add-data images/*;images --add-data *.png;. --add-data *.ico;. -w -i pronterface.ico pronterface.py

echo *******************************
echo ****** Build Pronterface ******
echo *******************************
pyinstaller --clean pronterface.spec -y

echo ********************************
echo ****** Add language files ******
echo ********************************
xcopy locale dist\locale\ /Y /E

echo ***************************************************************
echo ******                Batch finalizes                    ******
echo ******                                                   ******
echo ******    Happy printing with Pronterface for Windows!   ******
echo ******                                                   ******
echo ****** You will find Pronterface and localizations here: ******
echo ***************************************************************
cd dist
dir .
pause
echo on