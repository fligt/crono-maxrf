# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/30_Gridify-by-selection.ipynb.

# %% auto 0
__all__ = ['gridify']

# %% ../notebooks/30_Gridify-by-selection.ipynb 24
# python package for reading hdf5 files 
import h5py 

# python package for processing too-big-for-memory data 
import dask 
import dask.array as da 
#import dask_ndfilters 
from dask.diagnostics import ProgressBar 

# standard imports  
import re 
import os

def gridify(crono_filename): 
    '''Export Crono maxrf file spectral data into regular spectral image hdf5 file. '''
    
    # Datamunger should be able to read these 
    MAXRF_IMAGE = '/spectra'
    MAXRF_ENERGIES = '/wavelength'

    with h5py.File(crono_filename, mode='r') as fh: 

        # read spectra and energies from hdf5 dataset into (lazy) dask arrays  
        spectra = fh['/XRF/Spectra']
        dask_spectra = da.from_array(spectra) 
        energies = fh['/XRF/EnergyVector']
        dask_energies = da.from_array(energies)

        # load selected indices into memory as numpy array 
        selected = fh['/XRF/SpectraSelectedIndex'][:,:,0]  
        dask_gridified = dask_spectra.vindex[selected] # dask (lazy) fancy indexing 

        # create filename for saving to 
        ptrn = '\.[^\.]*$'  
        repl = '_GRIDIFIED.HDF5'
        gridified_filename = re.sub(ptrn, repl, crono_filename)

        # write gridified spectral image to hdf5 file 
        print(f'Converting \'{crono_filename}\':\n')
        
        print(f'(1/2) Writing dataset \'{MAXRF_IMAGE}\' with shape {dask_gridified.shape} to hdf5 file...') 
        with ProgressBar(): 
            dask_gridified.to_hdf5(gridified_filename, MAXRF_IMAGE)

        # also write channel energies to hdf5 file 
        print(f'(2/2) Writing dataset \'{MAXRF_ENERGIES}\' with shape {dask_energies.shape} to hdf5 file...')
        with ProgressBar(): 
            dask_energies.to_hdf5(gridified_filename, MAXRF_ENERGIES)
            
        filesize_MB = os.path.getsize(gridified_filename) // 1e6
        print(f'File size: {filesize_MB} MB')
            
        return gridified_filename

