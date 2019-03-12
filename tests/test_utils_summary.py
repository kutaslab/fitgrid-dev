import fitgrid
from fitgrid.utils.summary import INDEX_NAMES, KEY_LABELS


def _get_epochs_fg():
    # pretend we are starting the pipeline with user epochs dataframe

    # generate fake data
    fake_epochs = fitgrid.generate(n_samples=5, n_channels=2, n_categories=2)
    epochs_df = fake_epochs.table
    chans = fake_epochs.channels

    # convert to fitgrid epochs object
    epochs_fg = fitgrid.epochs_from_dataframe(
        epochs_df.reset_index().set_index(['Epoch_idx', 'Time']),
        channels=chans,
        epoch_id="Epoch_idx",
        time='Time',
    )

    return epochs_fg


def test__lm_get_summaries_df():

    fgrid_lm = fitgrid.lm(
        _get_epochs_fg(), RHS="1 + continuous + categorical", n_cores=4
    )

    summaries_df = fitgrid.utils.summary._lm_get_summaries_df(fgrid_lm)
    fitgrid.utils.summary._check_summary_df(summaries_df)


def test__lmer_get_summaries_df():

    fgrid_lmer = fitgrid.lmer(
        _get_epochs_fg(), RHS="1 + continuous + (1 | categorical)", n_cores=4
    )

    summaries_df = fitgrid.utils.summary._lmer_get_summaries_df(fgrid_lmer)
    fitgrid.utils.summary._check_summary_df(summaries_df)


def test_summarize():
    """test main wrapper to scrape summaries from either lm or lmer grids"""

    n_cores = 12

    # modelers and RHSs
    tests = {
        "lm": [
            "1 + continuous + categorical",
            "1 + continuous",
            "1 + categorical",
            "1",
        ],
        "lmer": [
            "1 + continuous + (1 | categorical)",
            "1 + (1 | categorical)",
        ],
    }

    epochs_fg = _get_epochs_fg()

    # do it
    for modler, RHSs in tests.items():
        summaries_df = fitgrid.utils.summary.summarize(
            epochs_fg,
            modler,
            LHS=epochs_fg.channels,
            RHS=RHSs,
            n_cores=n_cores,
        )
        assert summaries_df.index.names == INDEX_NAMES
        assert set(KEY_LABELS).issubset(set(summaries_df.index.levels[-1]))

    return summaries_df


def test__get_AICs():
    """stub"""

    RHSs = [
        "1 + continuous + categorical",
        "1 + continuous",
        "1 + categorical",
    ]

    epochs_fg = _get_epochs_fg()
    summaries_df = fitgrid.utils.summary.summarize(
        epochs_fg, 'lm', LHS=epochs_fg.channels, RHS=RHSs
    )

    aics = fitgrid.utils.summary._get_AICs(summaries_df)
    return aics


def test_smoke_plot_betas():
    """TO DO: needs argument testing"""

    summary_df = test_summarize()
    fitgrid.utils.summary.plot_betas(
        summary_df=summary_df,
        LHS=[col for col in summary_df.columns if "channel" in col],
    )


def test_smoke_plot_AICs():

    summary_df = test_summarize()
    figs = fitgrid.utils.summary.plot_AICmin_deltas(summary_df)
