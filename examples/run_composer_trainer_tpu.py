# Copyright 2022 MosaicML Composer authors
# SPDX-License-Identifier: Apache-2.0

"""Entrypoint that runs the Composer trainer on a provided YAML hparams file.

Adds a --datadir flag to conveniently set a common
data directory for both train and validation datasets.

Example that trains MNIST with label smoothing::

    >>> python examples/run_composer_trainer.py
    -f composer/yamls/models/classify_mnist_cpu.yaml
    --algorithms label_smoothing --alpha 0.1
    --datadir ~/datasets
"""
import sys
import tempfile
import warnings
from typing import Type

from composer.loggers.logger import LogLevel
from composer.loggers.logger_hparams import WandBLoggerHparams
from composer.trainer import TrainerHparams
from composer.utils import dist



#def main() -> None:
def t():
    

    if len(sys.argv) == 1:
        sys.argv = [sys.argv[0], "--help"]

    hparams = TrainerHparams.create(cli_args=True)  # reads cli args from sys.argv

    # if using wandb, store the config inside the wandb run
    for logger_hparams in hparams.loggers:
        if isinstance(logger_hparams, WandBLoggerHparams):
            logger_hparams.config = hparams.to_dict()
            
    trainer = hparams.initialize_object()
    #import pdb; pdb.set_trace()
    
    if dist.get_global_rank() == 0:
        with tempfile.NamedTemporaryFile(mode="x+") as f:
            f.write(hparams.to_yaml())
            trainer.logger.file_artifact(LogLevel.FIT,
                                         artifact_name=f"{trainer.logger.run_name}/hparams.yaml",
                                         file_path=f.name,
                                         overwrite=True)
    import torch_xla.core.xla_model as xm
    xm.rendezvous('once')
            
    trainer.fit()

    
def _mp_fn(index):
    t()
    
if __name__ == "__main__":

    import torch_xla.distributed.xla_multiprocessing as xmp
    xmp.spawn(_mp_fn, args=(), nprocs=8, start_method='fork')
    #main()
