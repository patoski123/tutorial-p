stage('Run BDD Tests') {
    parallel {
        stage('API BDD Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/bdd/test_api_features.py -v -n ${params.PARALLEL_WORKERS} --html=reports/html/api_bdd_report.html --json-report --json-report-file=reports/json/api_bdd_report.json
                '''
            }
        }
        stage('UI BDD Tests') {
            when {
                anyOf {
                    expression { params.TEST_TYPE == 'ui' }
                    expression { params.TEST_TYPE == 'smoke' }
                    expression { params.TEST_TYPE == 'regression' }
                }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/bdd/test_ui_features.py -v --html=reports/html/ui_bdd_report.html --json-report --json-report-file=reports/json/ui_bdd_report.json
                '''
            }
        }
        stage('Integration BDD Tests') {
            when {
                expression { params.TEST_TYPE == 'regression' }
            }
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/bdd/test_integration_features.py -v --html=reports/html/integration_bdd_report.html --json-report --json-report-file=reports/json/integration_bdd_report.json
                '''
            }
        }
    }
}


# Run all BDD tests
pytest tests/bdd/ -v

# Run only API BDD tests
pytest tests/bdd/test_api_features.py -v

# Run specific feature
pytest tests/bdd/ -k "authentication" -v

# Run by BDD markers
pytest -m "api and authentication" -v

# Run smoke BDD tests only
pytest -m "smoke and bdd" -v

# Generate BDD report
pytest tests/bdd/ --html=reports/html/bdd_report.html --self-contained-html

# Run with Gherkin terminal reporter
pytest tests/bdd/ --gherkin-terminal-reporter -v

# Run specific scenario by name
pytest tests/bdd/ -k "Successful login with valid credentials" -v