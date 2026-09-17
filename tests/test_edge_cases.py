def test_unknown_equipment_or_step(engine):
    obs = {
        'phe_id': 'UNKNOWN_PHE',
        'process_step': 'CAUSTIC'
    }
    result = engine.evaluate(obs)
    assert result['status'] == 'error'
    assert 'No baseline data' in result['message']
    
def test_missing_features(engine):
    # Should calculate score on remaining features
    obs = {
        'phe_id': 'PHE01',
        'process_step': 'CAUSTIC',
        'flow_lph': 30000.0  # missing temp_in and conductivity
    }
    result = engine.evaluate(obs)
    assert result['status'] == 'success'
    
    # We should have a low coverage
    coverage_str = result['data_coverage']
    scored = int(coverage_str.split(' ')[0])
    assert scored == 1
    
def test_grading(engine):
    # Test grade boundaries by manipulating deviations directly
    
    # Test A
    score, grade = engine.health_calc.calculate_health({'flow_lph': 0.5})
    assert grade == 'A'
    
    # Test B
    score, grade = engine.health_calc.calculate_health({'flow_lph': 2.5})
    assert grade == 'B'
    
    # Test F
    score, grade = engine.health_calc.calculate_health({'flow_lph': 8.0})
    assert grade == 'F'
