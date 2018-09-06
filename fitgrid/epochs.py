import pandas as pd
from statsmodels.formula.api import ols
# this ensures access to tqdm.pandas()
# see tqdm.autonotebook for details
from tqdm._tqdm_notebook import tqdm_notebook as tqdm

from .errors import FitGridError
from .fitgrid import FitGrid
from . import plots


class Epochs:
    """Container class used for storing epochs tables and exposing statsmodels.

    Parameters
    ----------

    epochs_table : pandas DataFrame
    """

    def __init__(self, epochs_table):

        from . import EPOCH_ID, TIME

        if not isinstance(epochs_table, pd.DataFrame):
            raise FitGridError('epochs_table must be a Pandas DataFrame.')

        # these index columns are required for consistency checks
        assert (TIME in epochs_table.index.names
                and EPOCH_ID in epochs_table.index.names)

        # now need to only keep EPOCH_ID in index
        # this is done so that any series that we get from fits are indexed on
        # EPOCH_ID only
        levels_to_remove = set(epochs_table.index.names)
        levels_to_remove.discard(EPOCH_ID)

        # so we remove all levels from index except EPOCH_ID
        epochs_table.reset_index(list(levels_to_remove), inplace=True)
        assert epochs_table.index.names == [EPOCH_ID]

        self.table = epochs_table
        snapshots = epochs_table.groupby(TIME)

        # check that snapshots across epochs have equal index by transitivity
        prev_group = None
        for idx, cur_group in snapshots:
            if prev_group is not None:
                if not prev_group.index.equals(cur_group.index):
                    raise FitGridError(
                        f'Snapshot {idx} differs from '
                        f'previous snapshot in {EPOCH_ID} index:\n'
                        f'Current snapshot\'s indices:\n'
                        f'{cur_group.index}\n'
                        f'Previous snapshot\'s indices:\n'
                        f'{prev_group.index}'
                    )
            prev_group = cur_group

        if not prev_group.index.is_unique:
            raise FitGridError(
                f'Duplicate values in {EPOCH_ID} index not allowed:'
                f'\n{prev_group.index}'
            )

        # we're good, set instance variable
        self.snapshots = snapshots

    def lm(self, LHS='default', RHS=None):

        if LHS == 'default':
            from . import CHANNELS
            LHS = CHANNELS

        # validate LHS
        if not (isinstance(LHS, list) and
                all(isinstance(item, str) for item in LHS)):
            raise FitGridError('LHS must be a list of strings.')

        assert set(LHS).issubset(set(self.table.columns))

        # validate RHS
        if RHS is None:
            raise FitGridError('Specify the RHS argument.')
        if not isinstance(RHS, str):
            raise FitGridError('RHS has to be a string.')

        def regression(data, formula):
            return ols(formula, data).fit()

        results = {}
        for channel in tqdm(LHS, desc='Overall: '):
            tqdm.pandas(desc=channel)
            results[channel] = self.snapshots.progress_apply(
                    regression,
                    formula=channel + ' ~ ' + RHS
            )
        grid = pd.DataFrame(results)

        return FitGrid(grid)

    def mlm():
        raise NotImplementedError

    def glm():
        raise NotImplementedError

    def plot_averages(self, channels=None):

        from . import CHANNELS
        if channels is None:
            if set(CHANNELS).issubset(set(self.table.columns)):
                channels = CHANNELS
            else:
                raise FitGridError('Default channels missing in epochs table,'
                                   ' please pass list of channels.')
        data = self.snapshots.mean()
        plots.stripchart(data[channels])