import sys
import os

this_path = os.path.dirname(os.path.realpath(__file__))
root_path = os.path.abspath(os.path.join(this_path, os.pardir, os.pardir))
sys.path.append(root_path)

from torch.optim import Adam
from utilities.training.trainer import Trainer
from utilities.paths import resources_path
from datasets.light import LightDataset
from modules.loss import LightLoss
from models.vggpt2v2.model import VGGPTv2, gpt2_tokenizer
import torch


def train(batch_size=20):
    basepath = os.path.join('models', 'vggpt2v2')

    loss = LightLoss(pad_token_id=gpt2_tokenizer._convert_token_to_id('-'))
    model = VGGPTv2()
    tr_dataset = LightDataset(resources_path(os.path.join(basepath, 'data')))
    ts_dataset = LightDataset(resources_path(os.path.join(basepath, 'data')), split='testing')

    learning_rate = 5e-5
    epochs = 20
    batch_size = batch_size

    trainer = Trainer(
        wandb_args={'project': 'vggpt2v2', 'name': 'vggpt2v2'},
        model=model,
        tr_dataset=tr_dataset,
        ts_dataset=ts_dataset,
        optimizer=Adam(model.parameters(), lr=learning_rate),
        loss=loss,
        epochs=epochs,
        num_workers=4,
        checkpoint_path=resources_path(basepath, 'checkpoints', 'latest'),
        device='cuda',
        shuffle=True,
        log_interval=10,
        lr=learning_rate,
        batch_size=batch_size
    )

    trainer.run()


if __name__ == '__main__':

    batch_size = input('Batch size? [20]: ')
    if batch_size != '':
        train(batch_size=int(batch_size))
    else:
        train()
