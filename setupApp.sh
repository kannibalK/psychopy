echo DID YOU UPDATE THE CHANGELOG?
sudo python setup.py sdist #create the tar.gz version
sudo python setup.py egg_info #to upload info to pypi
sudo python setup.py bdist_egg #an egg file for distribution
#then handle the mac app bundle
rm psychopy/demos/*.pyc
#cd psychopy/app
sudo rm -r build
sudo rm -r dist/PsychoPy.app
python setupApp.py py2app #don't run this as sudo