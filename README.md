# Reach-Sentinel-Lite


Quick start
-----------

1. First, download Django from the Django website, ideally for python-3: https://www.djangoproject.com/

2. Download the repo to a dedicated directory, ideally called **Reach-Sentinel-Lite**
	 - `git init`
	 - `git clone https://github.com/Bruin-Spacecraft-Group/Reach-Sentinel-Lite`

3. You should now see the files in your directory

4. Navigate into the repo you just cloned, then go into **reachSentinelLite**

5. To start the server, run: `python3 manage.py runserver`
	 - You can also use simple `python` to use python-2

6. Open a browser and navigate to: http://127.0.0.1:8000/testGraph/

7. The above link is the base page. For a more fancier view (if you want to compare two graphs at the same time): http://127.0.0.1:8000/dashboard/

8. If your website isn't working, it may mean that the database has not been initialized.
	 - `python3 manage.py makemigrations`
	 - `python3 manage.py migrate`

Next steps
-----------

1. We need to read data from serial and save to database

2. Update graphs everytime database is updated
	 - or every 1 second, whatever the optimal solution is
