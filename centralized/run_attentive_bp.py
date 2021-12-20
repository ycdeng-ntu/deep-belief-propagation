import os

import torch

from centralized.attentive_bp_entities import AttentiveFactorGraph, FeatureConstructor
from centralized.model import AttentiveBP
from centralized.utilities import elementwise_add


def run(model_path, problem_dir_path, nb_timestep=100, device ='cpu', scale=10):
    m = AttentiveBP(8, 16, 1, 7, 1, 8, 4)
    m.load_state_dict(torch.load(model_path, map_location=device))
    m.to(device)
    m.eval()
    cost_in_cycle = [0] * nb_timestep
    best_cost_in_cycle = [0] * nb_timestep
    cnt = 0
    for f in os.listdir(problem_dir_path):
        if not f.endswith('xml'):
            continue
        cnt += 1
        fg = AttentiveFactorGraph(os.path.join(problem_dir_path, f), scale=scale)
        fe = FeatureConstructor(fg.variable_nodes.values(), fg.function_nodes, ass_to_sum_hidden=7, device=device)
        cic = []
        bcic = []
        for ts in range(nb_timestep):
            c, _ = fg.step(m, fe, False, ts == 0)
            c = int(c * scale)
            cic.append(c)
            if len(bcic) == 0:
                bcic.append(c)
            else:
                bcic.append(min(bcic[-1], c))
        print(f, bcic[-1])
        cost_in_cycle = elementwise_add(cic, cost_in_cycle)
        best_cost_in_cycle = elementwise_add(bcic, best_cost_in_cycle)
    return [x / cnt for x in cost_in_cycle], [x / cnt for x in best_cost_in_cycle]


if __name__ == '__main__':
    for i in range(100, 10001, 100):
        c, bc = run(f'../top10_uniform_loss_models/{i}.pth', f'../problem_instance/grid/test/12', device='cuda:2')
        with open(f'../top10_uniform_loss_models/12_grid_cic.txt', 'a') as rf:
            rf.write(str(c) + '\n')
        with open(f'../top10_uniform_loss_models/12_grid_bcic.txt', 'a') as rf:
            rf.write(str(bc) + '\n')
        print(i, 'done')