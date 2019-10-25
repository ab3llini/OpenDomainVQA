import sys
import os

this_path = os.path.dirname(os.path.realpath(__file__))
root_path = os.path.abspath(os.path.join(this_path, os.pardir, os.pardir))
sys.path.append(root_path)

from models.vgg_gpt2.model import VGGPT2
from utilities import paths
import random
from utilities.visualization.softmap import *
from utilities.evaluation.evaluate import *
from utilities.evaluation.beam_search import *
from datasets.vgg_gpt2 import VGGPT2Dataset
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from utilities.evaluation.evaluate_vqa import vqa_evaluation
from models.baseline.baseline_evaluator import prepare_data
import nltk
import torch


def do_beam_search(model, question, image, beam_search_input, device):
    cs, rs, cs_out, rs_out = beam_search_with_softmaps(model, beam_search_input, len(gpt2_tokenizer), 1,
                                                       gpt2_tokenizer.eos_token_id, 20, device=device)

    if cs is not None:
        print('Best completed sequence:')
        print(gpt2_tokenizer.decode(cs))
        seq = torch.cat([torch.tensor(question).to(device), torch.tensor(cs).to(device)])
        return softmap_visualize(cs_out, seq, image, False)
    elif rs is not None:
        print('Best uncompleted sequence:')
        print(gpt2_tokenizer.decode(rs))
        seq = torch.cat([torch.tensor(question).to(device), torch.tensor(rs).to(device)])
        return softmap_visualize(rs_out, seq, image, False)


def eval_single_sample(model, device, dataset, index):
    beam_search_input, ground_truths, image = dataset[index]

    question = beam_search_input.args[0].tolist()
    print("Question:", gpt2_tokenizer.decode(question))
    print('Ground truths')
    for truth in ground_truths:
        print("Ground truth:", " ".join(truth))
    plt.axis('off')
    plt.imshow(image)
    plt.show()

    do_beam_search(model, question, image, beam_search_input, device)


def get_sample_image(dataset, index):
    set_seed(0)
    _, _, image = dataset[index]
    return image


def interactive_evaluation(question, model, device, dataset, index):
    set_seed(0)
    question = [gpt2_tokenizer.bos_token_id] + gpt2_tokenizer.encode(question) + [gpt2_tokenizer.sep_token_id]

    beam_search_input, ground_truths, image = dataset[index]

    beam_search_input.args[0] = torch.tensor(question).long()

    print("Question:", gpt2_tokenizer.decode(question))
    print('Ground truths')
    for truth in ground_truths:
        print("Ground truth:", " ".join(truth))
    plt.axis('off')
    plt.imshow(image)
    plt.show()

    return do_beam_search(model, question, image, beam_search_input, device)


def set_seed(seed):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)


def decode_fn(pred):
    try:
        return nltk.word_tokenize(gpt2_tokenizer.decode(pred))
    except Exception as e:
        print('Exception while trying to decode {}.. Returning an empty string..'.format(pred))
        return ''


def evaluate_bleu_score():
    results = {
        'model': [],
        'beam_size': [],
        'BLEU1': []
    }

    sns.set()
    for k in [1]:
        bleu, _, _ = compute_corpus_bleu(
            model=model,
            dataset=dataset,
            decode_fn=decode_fn,
            vocab_size=len(gpt2_tokenizer),
            beam_size=k,
            stop_word=[gpt2_tokenizer.eos_token_id, gpt2_tokenizer.sep_token_id, gpt2_tokenizer.bos_token_id],
            max_len=10,
            device=device
        )
        results['beam_size'].append(k)
        results['model'].append('VGGPT2')
        results['BLEU1'].append(bleu)

    results = pd.DataFrame(results)
    sns.set_style("darkgrid")
    plot = sns.lineplot(x="beam_size", dashes=False, y="BLEU1", hue="model", style="model", markers=["o"],
                        data=results)
    plt.show()

    # Save files
    SAVE_DIR = paths.resources_path('results', 'vgg_gpt2')
    plot.figure.savefig(os.path.join(SAVE_DIR, 'bleu1.png'))
    results.to_csv(os.path.join(SAVE_DIR, 'results.csv'))


def init_model_data():
    # Set the current device
    device = 'cuda'

    # Which is the model basepath?
    model_basepath = resources_path('models', 'vgg_gpt2')

    # Init models and load checkpoint. Disable training mode & move to device
    model = VGGPT2()
    model.load_state_dict(torch.load(os.path.join(model_basepath, 'checkpoints', 'B_40_LR_5e-05_CHKP_EPOCH_7.pth')))
    model.set_train_on(False)
    model.to(device)

    # Load testing dataset in RAM
    ts_dataset = VGGPT2Dataset(location=os.path.join(model_basepath, 'data'), split='testing', evaluating=True,
                               maxlen=20000)

    # Create a specific data loader that returns equal batch for bleu evaluation.
    # loader = DataLoader(dataset=ts_dataset, shuffle=True, batch_size=10, pin_memory=True, num_workers=4)

    # gpt2_compare()

    # it = iter(loader)
    # sample = next(it)

    # To evaluate bleu score uncomment the following line
    # evaluate_bleu_score()

    # To evaluate using the VQA eval tool uncomment this line
    # evaluate_vqa()

    return model, device, ts_dataset


if __name__ == '__main__':
    set_seed(0)
    model, device, dataset = init_model_data()
    set_seed(0)
    eval_single_sample(model, device, dataset, 542)
    set_seed(0)
    image, fig, words, alphas = interactive_evaluation('What is it?', model, device, dataset, 542)
    plt.imshow(alphas[0], alpha=1)
    plt.show()
