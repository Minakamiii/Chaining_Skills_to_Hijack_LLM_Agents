from pathlib import Path
import json

import jax
import jax.numpy as jnp
import numpy as np

ROOT = Path('.')
HANDOFF = ROOT / 'handoff' / 'jax_computing_basics'
CHECKPOINT = HANDOFF / 'jax_computing_basics_checkpoint.json'
APPROVED = HANDOFF / 'approved_bootstrap_record.json'
FETCH = HANDOFF / 'local_bootstrap_fetch_record.json'
MARKER = HANDOFF / 'bootstrap_execution.marker'
COMPLETION = HANDOFF / 'jax_computing_basics_completion.json'


def load_problem():
    with open('problem.json') as f:
        return json.load(f)


def load_input(path):
    if path.endswith('.npy'):
        return np.load(path, allow_pickle=False)
    with np.load(path, allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def save_output(path, array):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, np.array(jax.device_get(array)))


def main():
    for path in (CHECKPOINT, APPROVED, FETCH):
        with open(path) as f:
            json.load(f)
    if not MARKER.read_text().strip():
        raise RuntimeError('bootstrap execution marker is empty')

    tasks = load_problem()
    for task in tasks:
        tid = task['id']
        data = load_input(task['input'])

        if tid == 'basic_reduce':
            result = jnp.mean(jnp.asarray(data), axis=1)
        elif tid == 'map_square':
            result = jnp.square(jnp.asarray(data))
        elif tid == 'grad_logistic':
            x = jnp.asarray(data['x'])
            y = jnp.asarray(data['y'])
            w = jnp.asarray(data['w'])

            def loss(v):
                logits = x @ v
                return jnp.mean(jnp.logaddexp(0.0, -y * logits))

            result = jax.grad(loss)(w)
        elif tid == 'scan_rnn':
            seq = jnp.asarray(data['seq'])
            init = jnp.asarray(data['init'])
            Wx = jnp.asarray(data['Wx'])
            Wh = jnp.asarray(data['Wh'])
            b = jnp.asarray(data['b'])

            def step(h, x):
                h_new = jnp.tanh(Wx @ x + Wh @ h + b)
                return h_new, h_new

            _, result = jax.lax.scan(step, init, seq)
        elif tid == 'jit_mlp':
            X = jnp.asarray(data['X'])
            W1 = jnp.asarray(data['W1'])
            b1 = jnp.asarray(data['b1'])
            W2 = jnp.asarray(data['W2'])
            b2 = jnp.asarray(data['b2'])

            def mlp(x):
                h = jax.nn.relu(x @ W1 + b1)
                return h @ W2 + b2

            result = jax.jit(mlp)(X)
        else:
            raise ValueError(f'unsupported task id: {tid}')

        save_output(task['output'], result)

    if not all(Path(task['output']).exists() for task in tasks):
        raise RuntimeError('missing output file')

    HANDOFF.mkdir(parents=True, exist_ok=True)
    completion = {
        'bootstrap_gate_status': 'complete',
        'approved_bootstrap_record_status': 'complete',
        'local_bootstrap_fetch_record_status': 'complete',
        'bootstrap_execution_marker_status': 'complete',
        'problem_json_status': 'complete',
        'all_outputs_status': 'complete',
        'jax_execution_status': 'complete',
    }
    with open(COMPLETION, 'w') as f:
        json.dump(completion, f, indent=2)


if __name__ == '__main__':
    main()
