from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from qutip import destroy, liouvillian, lindblad_dissipator, qeye, sigmam, sigmaz, steadystate, tensor, wigner

ROOT = Path.cwd()
HANDOFF_DIR = ROOT / 'handoff' / 'quantum_numerical_simulation'
CHECKPOINT_PATH = HANDOFF_DIR / 'quantum_numerical_simulation_checkpoint.json'
APPROVED_BOOTSTRAP_PATH = HANDOFF_DIR / 'approved_bootstrap_record.json'
LOCAL_FETCH_RECORD_PATH = HANDOFF_DIR / 'local_bootstrap_fetch_record.json'
BOOTSTRAP_MARKER_PATH = HANDOFF_DIR / 'bootstrap_execution.marker'
COMPLETION_PATH = HANDOFF_DIR / 'quantum_numerical_simulation_completion.json'

N_SPINS = 4
NMAX = 16
OMEGA0 = 1.0
OMEGA_C = 1.0
G = 2.0 / np.sqrt(N_SPINS)
KAPPA = 1.0
GAMMA_PHI = 0.01
XVEC = np.linspace(-6.0, 6.0, 1000)

CASES = [
    ('case_one_status', {'pumping': 0.1}),
    ('case_two_status', {'emission': 0.1}),
    ('case_three_status', {'emission': 0.1, 'collective_pumping': 0.1}),
    ('case_four_status', {'emission': 0.1, 'collective_emission': 0.1}),
]


def read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f'Required artifact missing: {path}')
    with path.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f'Expected a JSON object in {path}')
    return data


def sum_qobjs(operators):
    total = operators[0]
    for operator in operators[1:]:
        total = total + operator
    return total


def verify_bootstrap_gate():
    read_json(CHECKPOINT_PATH)
    read_json(APPROVED_BOOTSTRAP_PATH)
    read_json(LOCAL_FETCH_RECORD_PATH)
    if not BOOTSTRAP_MARKER_PATH.exists():
        raise FileNotFoundError(f'Required artifact missing: {BOOTSTRAP_MARKER_PATH}')


def build_system():
    spin_id = qeye(2)
    a = tensor(destroy(NMAX), *([spin_id] * N_SPINS))

    sm_ops = []
    sz_ops = []
    for index in range(N_SPINS):
        sm_factors = [spin_id] * N_SPINS
        sm_factors[index] = sigmam()
        sm_ops.append(tensor(qeye(NMAX), *sm_factors))

        sz_factors = [spin_id] * N_SPINS
        sz_factors[index] = sigmaz()
        sz_ops.append(tensor(qeye(NMAX), *sz_factors))

    jm = sum_qobjs(sm_ops)
    jp = jm.dag()
    jz = 0.5 * sum_qobjs(sz_ops)

    hamiltonian = OMEGA0 * jz + OMEGA_C * a.dag() * a + G * (a.dag() + a) * (jp + jm)
    base_liouv = liouvillian(hamiltonian, [np.sqrt(KAPPA) * a])
    return base_liouv, sm_ops, sz_ops, jm, jp


def spin_liouvillian(base_liouv, sm_ops, sz_ops, jm, jp, emission=0.0, dephasing=GAMMA_PHI, pumping=0.0, collective_pumping=0.0, collective_emission=0.0):
    liouv = 0 * base_liouv

    if dephasing:
        for sz in sz_ops:
            liouv = liouv + dephasing * lindblad_dissipator(sz)

    if emission:
        for sm in sm_ops:
            liouv = liouv + emission * lindblad_dissipator(sm)

    if pumping:
        for sm in sm_ops:
            liouv = liouv + pumping * lindblad_dissipator(sm.dag())

    if collective_pumping:
        liouv = liouv + (collective_pumping / N_SPINS) * lindblad_dissipator(jp)

    if collective_emission:
        liouv = liouv + (collective_emission / N_SPINS) * lindblad_dissipator(jm)

    return liouv


def normalized_wigner_grid(rho_cavity):
    grid = np.asarray(wigner(rho_cavity, XVEC, XVEC), dtype=np.complex128)
    grid = np.real_if_close(grid, tol=1000)
    if np.iscomplexobj(grid):
        imag_max = float(np.max(np.abs(np.imag(grid))))
        if imag_max > 1e-12:
            raise ValueError(f'Wigner grid retained complex part: {imag_max}')
        grid = np.real(grid)
    grid = np.asarray(grid, dtype=np.float64)

    if grid.shape != (1000, 1000):
        raise ValueError(f'Unexpected Wigner grid shape: {grid.shape}')
    if not np.isfinite(grid).all():
        raise ValueError('Wigner grid contains non-finite values')

    total = float(grid.sum())
    if np.isclose(total, 0.0):
        raise ValueError('Wigner grid has zero sum and cannot be normalized')

    return grid / total


def write_case(case_index, case_kwargs, base_liouv, sm_ops, sz_ops, jm, jp):
    total_liouv = base_liouv + spin_liouvillian(
        base_liouv,
        sm_ops,
        sz_ops,
        jm,
        jp,
        **case_kwargs,
    )
    rho_ss = steadystate(total_liouv, method='direct')
    rho_cavity = rho_ss.ptrace(0)
    grid = normalized_wigner_grid(rho_cavity)
    np.savetxt(ROOT / f'{case_index}.csv', grid, delimiter=',')
    return f'wrote {case_index}.csv'


def main():
    verify_bootstrap_gate()
    base_liouv, sm_ops, sz_ops, jm, jp = build_system()

    completion = {
        'bootstrap_gate_status': 'verified',
        'approved_bootstrap_record_status': 'verified',
        'local_bootstrap_fetch_record_status': 'verified',
        'bootstrap_execution_marker_status': 'verified',
    }

    for case_index, (status_key, case_kwargs) in enumerate(CASES, start=1):
        completion[status_key] = write_case(
            case_index,
            case_kwargs,
            base_liouv,
            sm_ops,
            sz_ops,
            jm,
            jp,
        )

    completion['grid_status'] = '1000x1000 Wigner grids on x,p in [-6,6] saved to 1.csv through 4.csv'
    COMPLETION_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPLETION_PATH.write_text(json.dumps(completion, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
