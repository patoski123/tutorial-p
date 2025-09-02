pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    skipDefaultCheckout(false)
  }

  parameters {
    choice(name: 'MARKERS', choices: ['authentication', 'api', 'ui', 'e2e', 'smoke', 'regression', 'all'], description: 'Pytest -m marker to run')
    string(name: 'ENV', defaultValue: 'dev', description: 'TEST_ENV / settings environment')
    string(name: 'WORKERS', defaultValue: 'auto', description: 'xdist workers (e.g. 4 or auto)')
    booleanParam(name: 'HEADED', defaultValue: false, description: 'Run browser headed (UI)')
    string(name: 'BROWSER_PATH', defaultValue: '', description: 'Optional custom Chrome/Chromium executable path')
    choice(name: 'ALLURE_ATTACH', choices: ['json', 'png', 'both', 'none'], description: 'What to attach to Allure for API steps')
  }

  environment {
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PYTHONDONTWRITEBYTECODE = '1'
    TEST_ENV = "${params.ENV}"
    ALLURE_API_ATTACH = "${params.ALLURE_ATTACH}"   // your ApiRecorder toggle
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Python Setup') {
      steps {
        sh '''
          python3 -V
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -U pip wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Playwright Browsers') {
      steps {
        sh '''
          . .venv/bin/activate
          python -m playwright install --with-deps chromium
        '''
      }
    }

    stage('Prepare .env') {
      steps {
        // Keep it minimal; extend if you want to inject secrets via Jenkins credentials
        writeFile file: '.env', text: "TEST_ENV=${params.ENV}\n"
        sh 'echo "Using TEST_ENV=${TEST_ENV}"'
      }
    }

    stage('Run Tests') {
      steps {
        script {
          def browserPathArg = params.BROWSER_PATH?.trim() ? "--browser-path=${params.BROWSER_PATH.trim()}" : ""
          def headedArg = params.HEADED ? "--headed" : ""
          def markers = params.MARKERS == 'all' ? '' : "-m ${params.MARKERS}"

          sh """
            . .venv/bin/activate
            pytest ${markers} -n ${params.WORKERS} \
              --clean-alluredir --alluredir=reports/allure-results \
              --env=${params.ENV} ${headedArg} ${browserPathArg} \
              -ra
          """
        }
      }
    }

    stage('Archive Reports') {
      steps {
        archiveArtifacts artifacts: 'reports/**/*', fingerprint: true, onlyIfSuccessful: false
      }
    }

    stage('Publish Allure') {
      steps {
        // Requires Allure Jenkins plugin
        allure includeProperties: false, jdk: '', results: [[path: 'reports/allure-results']]
      }
    }
  }

  post {
    always {
      // Keep workspace small between builds if you want
      echo 'Build finished.'
    }
    failure {
      echo 'Tests failed.'
    }
  }
}
