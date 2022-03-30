# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/30_Gridify-by-selection.ipynb (unless otherwise specified).

__all__ = ['read_datasets', 'report', 'peek_inside', 'gridify']

# Cell

import h5py
import numpy as np

def read_datasets(crono_filename):
    '''Read all datasets in `crono_filename`.'''

    fh = h5py.File(crono_filename, mode='r')

    groups_and_datasets = []
    fh.visit(groups_and_datasets.append)

    datasets = [fh[d] for d in groups_and_datasets if (type(fh[d]) == h5py.Dataset)]

    return datasets


def report(crono_filename):
    '''Print info about structure and content of datasets in `crono_filename`.'''

    datasets = read_datasets(crono_filename)

    # print list of datasets
    print(f'CONTENTS OF CRONO HDF5 FILE: \'{crono_filename}\'')
    print(f'({len(datasets)} DATASETS)\n')

    for i, d in enumerate(datasets):
        print(f'[{i}] {d.name}')

    print()

    ruler = '-'*80

    for i, d in enumerate(datasets):


        print(ruler)
        print(f'[{i}] ', end='')
        peek_inside(d)




def peek_inside(dataset, _print=True):
    '''Summarize structure and content of a `dataset`. '''

    shape_str, dtype, sub_dtype = _nesting(dataset)


    # simplify represention for certain complex dataset structures
    if dtype == np.dtype('S1'):
        value_str = ''.join(dataset[...].astype(str))

    elif sub_dtype == np.dtype('V1'):
        value_str = bytes(dataset[...][0])

    elif sub_dtype == np.dtype('S1'):
        str_list = [''.join(s.astype(str)) for s in dataset[...]]
        value_str = '\n'.join(str_list)

    # otherwise use default repr string
    else:
        value_str = repr(dataset[...])

    # compose summary
    name = dataset.name
    attributes = _get_attrs(dataset)

    summary = f'{name}:\n\n{attributes}\n{shape_str}\n\n+VALUES: \n\'{value_str}\'\n\n'

    if _print:
        print(summary)
        return None
    else:
        return summary


def _nesting(dataset):
    '''Report shape or nested shapes of numpy arrays in `dataset`.'''

    v = dataset[...]
    shape = v.shape
    dtype = v.dtype

    shape_str = f'+SHAPE: {v.shape} DTYPE: \'{v.dtype}\''

    sub_dtype = None

    if dtype == np.dtype('O'):

        subshape_list = [a.shape for a in v]
        sub_dtype = v[-1].dtype
        n_sub = len(subshape_list)

        if n_sub > 4:

            subshape_list = subshape_list[0:4]
            subshape_list.append(f'....')

        subshape_str = f'{subshape_list}'
        shape_str = shape_str + ' SUBSHAPES: ' + subshape_str + f' SUB_DTYPE: \'{sub_dtype}\''

    return shape_str, dtype, sub_dtype


def _get_attrs(dataset):
    '''Report information from `dataset` attributes.'''

    attr_items = dataset.attrs.items()
    attr_keys = []
    attr_values = []

    for k, v in attr_items:
        attr_keys.append(k)

        # get rid of outer array
        if v[0].dtype == np.dtype('S1'):
            v = ''.join(v[0].astype(str))
        if type(v) == np.ndarray:
            v = v[0]

        if k == 'MapSetup':
            v = bytes(v)

        if k == 'TubeTemperature':
            v = f'{v:0.2f}'

        attr_values.append(v)


    attr_dict = dict(zip(attr_keys, attr_values))

    if len(attr_dict) > 0:

        repr_string = '+ATTRIBUTES: \n'

        for k, v in attr_dict.items():

            repr_string = repr_string + f'        - {k}: {v}\n'

    else:
        repr_string = '+ATTRIBUTES: (none)\n'

    #print(repr_string)


    return repr_string

# Cell

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

    MAXRF_IMAGE = '/maxrf_image'
    MAXRF_ENERGIES = '/maxrf_energies'

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
