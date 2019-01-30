import pandas as pd
import pickle
import statsmodels
from statsmodels.regression.linear_model import (
    RegressionResults,
    RegressionResultsWrapper,
)
from .epochs import Epochs
from .fitgrid import FitGrid, LMFitGrid, LMERFitGrid
from .errors import FitGridError
from . import defaults


def epochs_from_hdf(hdf_filename, key, time, epoch_id, channels):
    """Construct Epochs object from an HDF5 file containing an epochs table.

    The HDF5 file should contain columns with names defined by EPOCH_ID and
    TIME either as index columns or as regular columns. This is added as a
    convenience, in general, input epochs tables should contain these columns
    in the index.

    Parameters
    ----------
    hdf_filename : str
        HDF5 file name
    key : str
        group identifier for the dataset when HDF5 file contains more than one
    channels : list of str, optional, defaults to CHANNELS
        list of string channel names

    Returns
    -------
    epochs : Epochs
        an Epochs object with the data
    """

    if None in (time, epoch_id, channels):
        raise FitGridError(
            'Please provide `time`, `epoch_id`, and `channels` parameters.'
            ' You can use the defaults, for example:\n'
            'time=fitgrid.defaults.TIME'
        )

    df = pd.read_hdf(hdf_filename, key=key)

    # time and epoch id already present in index
    if epoch_id in df.index.names and time in df.index.names:
        return Epochs(df, time=time, epoch_id=epoch_id, channels=channels)

    # time and epoch id present in columns, set index
    if epoch_id in df.columns and time in df.columns:
        df.set_index([epoch_id, time], inplace=True)
        return Epochs(df, time=time, epoch_id=epoch_id, channels=channels)

    raise FitGridError(
        f'Dataset has to contain {epoch_id} and {time} as columns or indices.'
    )


def epochs_from_dataframe(dataframe, time, epoch_id, channels):
    """Construct Epochs object from a Pandas DataFrame epochs table.

    The DataFrame should contain columns with names defined by EPOCH_ID and
    TIME as index columns.

    Parameters
    ----------
    dataframe : pandas DataFrame
        a pandas DataFrame object
    channels : list of str, optional, defaults to CHANNELS
        list of string channel names

    Returns
    -------
    epochs : Epochs
        an Epochs object with the data
    """
    return Epochs(dataframe, time=time, epoch_id=epoch_id, channels=channels)


def epochs_from_feather(filename, time, epoch_id, channels):
    """Construct Epochs object from a Feather file containing an epochs table.

    The file should contain columns with names defined by EPOCH_ID and TIME.

    Parameters
    ----------
    filename : str
        Feather file name
    channels : list of str, optional, defaults to CHANNELS
        list of string channel names

    Returns
    -------
    epochs : Epochs
        an Epochs object with the data
    """

    check_pandas_pyarrow_versions()

    df = pd.read_feather(filename)

    # time and epoch id present in columns, set index
    if epoch_id in df.columns and time in df.columns:
        df.set_index([epoch_id, time], inplace=True)
        return Epochs(df, time=time, epoch_id=epoch_id, channels=channels)

    raise FitGridError(
        f'Dataset has to contain {epoch_id} and {time} as columns or indices.'
    )


def load_grid(filename):
    """Load a FitGrid object from file (created by running grid.save).

    Parameters
    ----------
    filename : str
        indicates file to load from

    Returns
    -------
    grid : FitGrid
        loaded FitGrid object
    """

    from pymer4 import Lmer

    with open(filename, 'rb') as file:
        _grid, epoch_index, time = pickle.load(file)

    tester = _grid.iloc[0, 0]

    if isinstance(tester, (RegressionResults, RegressionResultsWrapper)):
        return LMFitGrid(_grid, epoch_index, time)
    elif isinstance(tester, Lmer):
        return LMERFitGrid(_grid, epoch_index, time)
    else:
        return FitGrid(_grid, epoch_index, time)


def check_pandas_pyarrow_versions():

    import pyarrow
    from pkg_resources import parse_version

    PANDAS_LAST_INCOMPATIBLE_VERSION = parse_version('0.23.4')
    PYARROW_LAST_INCOMPATIBLE_VERSION = parse_version('0.11.1')

    pandas_version = parse_version(pd.__version__)
    pyarrow_version = parse_version(pyarrow.__version__)

    have_incompatible_version = False

    msg = ''

    if pandas_version <= PANDAS_LAST_INCOMPATIBLE_VERSION:
        msg += (
            'Need at least pandas 0.24.0 to read Feather, '
            f'you have {str(pandas_version)}.\n'
        )
        have_incompatible_version = True

    if pyarrow_version <= PYARROW_LAST_INCOMPATIBLE_VERSION:
        msg += (
            'Need at least pyarrow 0.12.0 to read Feather, '
            f'you have {str(pyarrow_version)}.\n'
        )
        have_incompatible_version = True

    if have_incompatible_version:
        raise ImportError(msg)
