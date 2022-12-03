test = {
  'name': 'Question no_girls',
  'points': 5,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> # You need to set the value for 'p_no_girls'
          >>> 'p_no_girls' in vars()
          True
          """,
          'hidden': False,
          'locked': False
        },
        {
          'code': r"""
          >>> # You haven't changed the value for 'p_no_girls'
          >>> # from its initial state (of ...)
          >>> p_no_girls != ...
          True
          """,
          'hidden': False,
          'locked': False
        },
        {
          # # Take 10000 samples of 10000 trials of this problem.
          # n = 10000
          # res = np.sum(np.random.binomial(4, 0.5, (n, n)) == 0, axis=1) / n
          # print(np.min(res), np.max(res))
          'code': r"""
          >>> 0.051 < p_no_girls < 0.072
          True
          """,
          'hidden': False,
          'locked': False
        },
        #: begin-extra
        {
          'code': r"""
          >>> True
          True
          """,
          'hidden': False,
          'locked': False
        },
        #: end-extra
      ],
      'scored': True,
      'setup': '',
      'teardown': '',
      'type': 'doctest'
    }
  ]
}
