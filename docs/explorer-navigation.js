'use strict';
(function () {
  const scriptEl =
    document.currentScript ||
    document.querySelector('script[src*="explorer-navigation.js"]');
  const baseUrl = scriptEl
    ? new URL('.', scriptEl.src)
    : new URL('./', window.location.href);

  const CATEGORIES = [
    {title:'Saved results: measured and simulated',subtitle:'Separate evidence types; no new fits, simulations or molecular calibration.',items:[{id:'results-lab',title:'Organoid model & held-out rheology results',relPath:'results-lab/',geometry:'2D numerical plots with selected-record readouts',evidence:'156 synthetic gels / 210 rheology measurements',note:'Synthetic gene outputs and measured small-strain bovine hydrogel tests occupy separate tabs. Residuals are not predictive uncertainty.'}]},
    {
      title: 'Molecular backbones',
      subtitle:
        'Constructed triple-helical coordinate geometry only — no molecular dynamics, AGE reaction kinetics, or calibrated network stiffness.',
      items: [
        {
          id: 'species',
          title: 'Beaver & human molecular pilot',
          relPath: 'species.html',
          geometry: '3D triple-helix Cα backbone traces (CDSM)',
          evidence: 'Sequence-matched structural hypothesis · uncalibrated',
          note: 'Compares Castor canadensis and Homo sapiens COL1A1/COL1A2 windows; does not parameterize network springs.',
        },
      ],
    },
    {
      title: 'Planar network/damage hypotheses',
      subtitle:
        'Dimensionless 2D spring/beam networks, scalar mechanism sweeps, and linear harmonic probes — not calibrated to tissue age, clinical pressure limits, or 3D continuum mechanics.',
      items: [
        {
          id: 'original-atlas',
          title: 'Fracture Atlas (architectures & load angles)',
          relPath: 'index.html',
          geometry: '2D discrete fiber network (36 nodes, 82 edges)',
          evidence: 'Synthetic dimensionless benchmark',
          note: 'Seven network architectures under uniaxial, shear, compression, pulse, and rotated perimeter strain.',
        },
        {
          id: 'aging',
          title: 'Age-related crosslinks & density sweep',
          relPath: 'aging.html',
          geometry: '2D discrete network + effective connector springs',
          evidence: 'Synthetic mechanism test · no age-in-years scale',
          note: 'Tests distributed vs clustered added connectors on a fixed 2D skeleton across 6,300 saved configurations.',
        },
        {
          id: 'topology-aging',
          title: 'Why crosslink placement matters in aging',
          relPath: 'topology-aging.html',
          geometry: '2D network connectivity & placement maps',
          evidence: 'Saved 3-seed synthetic comparison',
          note: 'Contrasts stiffness and work-to-criterion tradeoffs between distributed and clustered crosslink placement.',
        },
        {
          id: 'transitions',
          title: 'Collagen mechanism transition atlas',
          relPath: 'transitions/',
          geometry: 'Scalar response curves from 2D networks, 2D disks & 1D/ODE models',
          evidence: 'Saved numerical sweeps · explicit invalid gaps',
          note: 'Strain-driven stiffness, sliding/locking, disk contact, bond cuts, LOX feedback ODE, and 81-site transfer matrix.',
        },
        {
          id: 'force-replay',
          title: 'Force redistribution & damage replay',
          relPath: 'force-replay/',
          geometry: '2D discrete network trajectory replay',
          evidence: 'Saved quasistatic step replay',
          note: 'Inspects fiber tension, compression, and rupture sequence across disordered and modular networks.',
        },
        {
          id: 'force-robustness',
          title: 'Force & damage robustness study',
          relPath: 'force-robustness/',
          geometry: '2D network ensemble & perturbation checks',
          evidence: 'Synthetic sensitivity & step-refinement audit',
          note: 'Tests how placement and solver discretization affect force redistribution before and after bond damage.',
        },
        {
          id: 'microrheology',
          title: 'Larger-network harmonic microrheology',
          relPath: 'microrheology/',
          geometry: '2D network (100 & 196 nodes) · uniform nodal drag',
          evidence: 'Linearized harmonic phasor calculation',
          note: 'Compares local and remote oscillatory compliance before and after a prescribed three-fiber lesion.',
        },
        {
          id: 'poroelasticity',
          title: 'Fluid-coupled poroelastic microrheology',
          relPath: 'poroelasticity/',
          geometry: '2D discrete network coupled to 2D FEniCSx Darcy pressure',
          evidence: 'Hybrid discrete-solid / Biot-fluid hypothesis test',
          note: 'Matched comparison of uniform drag vs continuum fluid pressure coupling across a local 3-fiber cut.',
        },
      ],
    },
    {
      title: '3D measured/predicted fields',
      subtitle:
        '3D continuum/lattice benchmarks calibrated to bulk rheology or evaluated against measured 3D PIV displacement fields — independent from the 2D synthetic fracture and aging networks.',
      items: [
        {
          id: 'evidence-atlas',
          title: 'Collagen Evidence Atlas (integrated 3D field & comparisons)',
          relPath: 'evidence-atlas/',
          geometry: '3D measured PIV vectors + side-by-side 2D synthetic labs',
          evidence: 'Conditional 3D benchmark (Pos 008 reused) + separate 2D studies',
          note: 'Inspects 3D observed/predicted/residual displacement fields alongside explicitly separated 2D crosslink and microrheology labs.',
        },
        {
          id: 'bovine-3d',
          title: 'Bovine-calibrated 3D comparator',
          relPath: 'bovine-3d/',
          geometry: '3D continuum / network comparator',
          evidence: 'Bulk rheological calibration · not fiber-resolved',
          note: 'Calibrates bulk response against published bovine collagen rheology without claiming single-fiber validation.',
        },
        {
          id: 'measured-3d',
          title: 'Measured 3D displacement validation',
          relPath: 'measured-3d/',
          geometry: '3D guarded interior displacement field (PIV)',
          evidence: 'Measured 3D boundary-value test',
          note: 'Evaluates interior displacement predictions conditioned on observed boundary motion.',
        },
        {
          id: 'nonlinear-3d',
          title: 'Nonlinear 3D benchmark (buckling vs sliding)',
          relPath: 'nonlinear-3d/',
          geometry: '3D displacement & strain-mismatch benchmark',
          evidence: 'Position 007 selected · Position 008 evaluated',
          note: 'Tests compression buckling and plastic sliding surrogates against harmonic interpolation in 3D.',
        },
      ],
    },
  ];

  function normalizePath(urlObj) {
    let p = urlObj.pathname.replace(/\/index\.html$/, '/');
    if (!p.endsWith('/') && !p.endsWith('.html')) p += '/';
    return p;
  }

  function isCurrentPage(targetUrl) {
    const curr = normalizePath(new URL(window.location.href));
    const targ = normalizePath(targetUrl);
    return curr === targ;
  }

  function el(tag, className, textContent) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (textContent !== undefined) node.textContent = textContent;
    return node;
  }

  function buildNavigation() {
    if (document.querySelector('.sc-explorer-nav')) return;

    const wrapper = el('aside', 'sc-explorer-nav');
    wrapper.setAttribute(
      'aria-label',
      'Related ScienceClaw collagen explorers and evidence levels',
    );

    const details = el('details', 'sc-explorer-nav__details');
    const summary = el('summary', 'sc-explorer-nav__summary');

    const sumTitleWrap = el('div', 'sc-explorer-nav__summary-main');
    sumTitleWrap.append(
      el('span', 'sc-explorer-nav__eyebrow', 'CROSS-EXPLORER RESEARCH MAP'),
      el(
        'span',
        'sc-explorer-nav__title',
        'Related collagen explorers by geometry & evidence type (13 studies)',
      ),
    );
    const sumHint = el(
      'span',
      'sc-explorer-nav__toggle-hint',
      'Separate models · Not a single validated multiscale simulator',
    );
    summary.append(sumTitleWrap, sumHint);
    details.append(summary);

    const body = el('div', 'sc-explorer-nav__body');
    const disclaimer = el(
      'p',
      'sc-explorer-nav__disclaimer',
      'Methodological boundary: Each explorer below isolates a specific geometry and evidence regime. Molecular Cα backbones, dimensionless 2D spring/poroelastic networks, and 3D PIV displacement benchmarks use distinct assumptions and units; they are not coupled into a validated multiscale tissue model.',
    );
    body.append(disclaimer);

    const grid = el('div', 'sc-explorer-nav__categories');
    for (const cat of CATEGORIES) {
      const section = el('section', 'sc-explorer-nav__category');
      section.append(
        el('h3', 'sc-explorer-nav__cat-title', cat.title),
        el('p', 'sc-explorer-nav__cat-sub', cat.subtitle),
      );
      const list = el('ul', 'sc-explorer-nav__list');
      for (const item of cat.items) {
        const targetUrl = new URL(item.relPath, baseUrl);
        const current = isCurrentPage(targetUrl);
        const li = el(
          'li',
          'sc-explorer-nav__item' + (current ? ' is-current' : ''),
        );

        const topRow = el('div', 'sc-explorer-nav__item-head');
        const link = el('a', 'sc-explorer-nav__link', item.title);
        link.href = targetUrl.href;
        if (current) {
          link.setAttribute('aria-current', 'page');
        }
        topRow.append(link);
        if (current) {
          topRow.append(el('span', 'sc-explorer-nav__here', 'Current page'));
        }

        const badges = el('div', 'sc-explorer-nav__badges');
        badges.append(
          el('span', 'sc-explorer-nav__badge geo', item.geometry),
          el('span', 'sc-explorer-nav__badge ev', item.evidence),
        );

        const note = el('p', 'sc-explorer-nav__note', item.note);
        li.append(topRow, badges, note);
        list.append(li);
      }
      section.append(list);
      grid.append(section);
    }
    body.append(grid);
    details.append(body);
    wrapper.append(details);

    const hook = document.getElementById('explorer-nav-root');
    if (hook) {
      hook.replaceWith(wrapper);
      return;
    }
    const main = document.querySelector('main');
    if (main) {
      main.append(wrapper);
      return;
    }
    const footer = document.querySelector('footer');
    if (footer && footer.parentNode) {
      footer.parentNode.insertBefore(wrapper, footer);
      return;
    }
    document.body.append(wrapper);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildNavigation);
  } else {
    buildNavigation();
  }
})();
