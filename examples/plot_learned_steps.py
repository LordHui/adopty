import numpy as np
import matplotlib.pyplot as plt


from adopty.lista import Lista
from adopty.datasets import make_coding


############################################
# Configure matplotlib and joblib cache
############################################
from joblib import Memory
from setup import colors, rc
plt.rcParams.update(rc)

mem = Memory(location='.', verbose=0)


###########################################
# Parameters of the simulation
###########################################
n_dim = 10
n_atoms = 20
n_samples = 1000
n_test = 1000
n_layers = 20
reg = 0.2
rng = 1
max_iter = 100


############################################
# Benchmark computation function
############################################
@mem.cache
def get_steps(n_dim, n_atoms, n_samples, n_test, n_layers, reg, rng, max_iter):
    lista_kwargs = dict(
        n_layers=n_layers,
        max_iter=max_iter)
    x, D, z = make_coding(n_samples=n_samples + n_test, n_atoms=n_atoms,
                          n_dim=n_dim, random_state=rng)
    x_test = x[n_samples:]
    x = x[:n_samples]

    L = np.linalg.norm(D, ord=2) ** 2  # Lipschitz constant
    network = Lista(D, **lista_kwargs,
                    parametrization='step', per_layer='oneshot')
    init_score = network.score(x_test, reg)
    print(init_score)
    network.fit(x, reg)
    print(network.score(x_test, reg))
    steps = network.get_parameters(name='step_size')
    L_s = np.zeros((n_layers, n_samples))
    for layer in range(1, n_layers+1):
        z_ = network.transform(x, reg, output_layer=layer)
        supports = z_ != 0
        S_pca = []
        for support in supports:
            idx = np.where(support)[0]
            D_s = D[idx]
            G_s = D_s.T.dot(D_s)
            S_pca.append(np.linalg.eigvalsh(G_s)[-1])
        L_s[layer-1] = np.array(S_pca)
    return steps, L, L_s, S_pca


############################################
# Run the benchmark
############################################
steps, L, L_S, S_pca = get_steps(n_dim, n_atoms, n_samples, n_test, n_layers,
                                 reg, rng, max_iter)


############################################
# Plot the results
############################################
ls_steps = 1 / L_S
ls_2_steps = 2 / L_S
n_quantiles = 11
quantiles = np.linspace(0, 0.95, n_quantiles)
# avg_ls = np.mean(ls_steps, axis=1)
quants = np.array([np.quantile(ls_steps, q, axis=1) for q in quantiles])
quants_2 = np.array([np.quantile(ls_2_steps, q, axis=1) for q in quantiles])
f, ax = plt.subplots(1, 1, figsize=(3, 2))
xlim = np.arange(1, n_layers + 1)
ax.plot(xlim, steps, color=colors['SLISTA'], label='Learned steps',
        linewidth=3)
ax.plot(xlim, quants[n_quantiles // 2], color='darkgoldenrod',
        label=r'$1/L_S$', linewidth=3)
ax.plot(xlim, quants_2[n_quantiles // 2], color='olivedrab',
        label=r'$2/L_S$', linewidth=3)
for i in range(n_quantiles // 2):
    ax.fill_between(xlim, quants[i], quants[n_quantiles - i - 1],
                    color='sandybrown', alpha=1.5 * (i + 1)/n_quantiles)
    ax.fill_between(xlim, quants_2[i], quants_2[n_quantiles - i - 1],
                    color='palegreen', alpha=1.5 * (i + 1)/n_quantiles)
ax.hlines(1 / L, 1, 9, color='k', linestyle='--')
ax.hlines(1 / L, 12, n_layers, color='k', linestyle='--')
ax.text(9, 1/L * 0.93, r'$1/L$')
# lgd_ = ax[0].legend(loc='upper left')
x_ = ax.set_xlabel('Layer')
y_ = ax.set_ylabel('Step')
# ax.yaxis.grid(True)
ax.set_xticks([1, 10, 20])
ax.set_xlim([1, n_layers])
ax.set_ylim([0.15, 1])
plt.yticks([1 / L, 2 / L, 3 / L, 4 / L],
           [r'$1/L$', r'$2/L$', r'$3/L$', r'$4/L$'])
# ax[1].hist(1 / np.array(S_pca), orientation='horizontal', bins=30,
#            density='normed', color='sandybrown', alpha=0.8,
#            histtype='bar', label=r'$\frac{1}{L_S}$')
# # ax[1].legend(handlelength=0.5)
# ax[1].set_xticks([])
# ax[1].set_ylim([0.18, 0.67])
# # plt.hlines(2 / L_S, 0, n_layers, color='b', linestyle='--',
# #            label=r'$\frac{2}{L_S}$')
lgd_ = f.legend(ncol=3, loc='upper center', handletextpad=0.1,
                handlelength=1, columnspacing=.8)
plt.subplots_adjust(top=0.75)
plt.savefig('figures/learned_steps.pdf',
            bbox_extra_artists=[lgd_, x_, y_],
            bbox_inches='tight')
plt.show()
