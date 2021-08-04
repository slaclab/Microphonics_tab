# Microphonics_tab
This is a pydm widget to run the microphonics script and then plot short runs for one cavity.
The four files uploaded are the main pydm file CommMicro.py (commissioning Microphonics) which is executed using the command 'pydm CommMicro.py'.  The main widget User interface is  "FFT_Test.ui" which shows the User inputs.  The User selects the length of the data acq, the cryomodule selected and a cavity.  For commissioning the interface only allows one cavity at a time, but the resonance chassis are capable of taking data for all 8 cavities simultaneously.  
The pull down menu allows the User to select how to display the data; either as a waterfall or fft. The data is displayed on the second User interface "MicPlot.ui". For longer acquisitions, where the files are much larger, no plot is given as an option to reduce loading of control computers.  
This is the version from the production servers. The subprocess call used freezes the display during the data acq and hasn't given up line by line stdout yet. The module  "dummyFileCreator" is available, but commented out which takes the path and existing dataset and generates a file for running the code on dev machines.  The directory structure is 
a 'microphonics' directory with sub-directories for every cavity for you to use:
>
> $PHYSICS_TOP/rf_lcls2/microphonics
>
> Under this, are the individual cavity directories, a few for example:
>
> ACCL_L1B_0310
> ACCL_L1B_0320
> ACCL_L1B_0330
> ACCL_L1B_0340
>
> (within the individual cavity directory) a new directory is created for each data
> set, formatted like this example:
>
> ACCL_L3B_1680_20210624_202608
>
> (<cavity>_<yearmonthday>_<hourminsec>)
>
> the data files are written to this directory. The suffix
> '_microphonics.dat' is added to each file, so it looks like the name below.  
>
> ACCL_L3B_1680_20210624_202608_microphonics.dat 
  
The FFt_math.py file has some of the math and file handling functions to separate them from the display and User interface.
