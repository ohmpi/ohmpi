Monitoring application
**********************

This section details ways to automate measurement acquisition in order to set up the OhmPi as a monitoring tool.

Repeated acquisition at fixed intervals
=======================================
The easiest way to set up time-lapse acquisition is to perform repeated acquisition of a sequence at fixed intervals.
Repeated acquisition can be initiated from the three different :ref:`interfaces`.

.. code-block:: python
  :caption: Example of code for monitoring.

  ### Run multiple sequences at given time interval
  k.settings['nb_meas'] = 3  # run sequence three times
  k.settings['sequence_delay'] = 100 # every 100 s
  k.run_multiple_sequences()  # asynchronous
  # k.interrupt()  # kill the asynchronous sequence

Scheduled acquisition using crontab
===================================
One can automate acquisitions by calling in a script via crontab (a LINUX built-in scheduler) at scheduled timings.
One way of achieving this is to rely on a python script detailing the desired operations (i.e. run_sequence, etc.),
which is called in a bash script. The bash script is needed here to activate the python environment (ohmpy) and
can potentially feature additional basic operations, such as selecting appropriate settings, or sending data to
a remote server.

.. code-block:: python
  :caption: Example of a python code (run_sequence.py) taking a sequence filename and a settings filename as arguments

  args = sys.argv
  if len(args) > 1 :
      sequence_filename = args[1]
      settings_filename = args[2]
  else:
      print("args missing")


  ### Define object from class OhmPi
  k = OhmPi()

  ### Set or load sequence
  k.load_sequence(sequence_filename)    # load sequence from a local file

  ### Run contact resistance check
  # k.rs_check()

  k.update_settings(settings_filename)

  ### Updating export_path to match sequence filename
  k.settings['export_path'] = os.path.join('data',os.path.split(sequence_filename.replace('.txt','.csv'))[1])

  ### Run sequence
  k.run_sequence() #save_strategy_fw=True) #plot_realtime_fulldata=True)


In this example, the prefix of the data filename (export_path) will match the prefix of the sequence filename.
This python script (called run_sequence.py) can be run in the terminal as follows:

.. code-block:: console

   python -m run_sequence.py my_sequence.csv my settings.json

Then a bash script is required to load in the python environment and calling the python script, such as:

.. code-block:: bash
    :caption: Example of a bash script (run_sequence.sh) calling in run_sequence.py

    #!bin/bash
    USER="pi"  # change if other username
    PROJECT="OhmPi"

    SURVEY=$(ls /home/$USER/$PROJECT/sequences/$1*)
    echo $SURVEY

    #Load settings
    cd /home/$USER/$PROJECT
    SETTINGS=$(ls settings/$2.json)

    #Load ohmpy environment
    source /home/$USER/$PROJECT/ohmpy/bin/activate

    #run python script
    python /home/$USER/$PROJECT/run_seq.py $SURVEY $SETTINGS

    #Add automatic processing scripts or transfer to backup serve, e.g.
    /usr/bin/rsync -avz -h /home/$USER/$PROJECT/data/$1* login@your_server.org:/path/to/copy/on/your/server

This script can then be added to a crontab scheduler by calling in

.. code-block:: console

   crontab -e

And updating the schedule according to your needs:

.. code-block:: bash
   :caption: Example of crontab entry

   # m h  dom mon dow   command
   0 12 * * * /usr/bin/bash /home/pi/OhmPi/run_sequence.sh my_sequence my_settings >> cronlog.log



IoT acquisition and sensor trigger
==================================
Example node-red experiment