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
    ALLURE_API_ATTACH = "${params.ALLURE_ATTACH}"
    # Optional: cache browsers between builds
    PLAYWRIGHT_BROWSERS_PATH = '.pw-browsers'
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Python Setup') {
      steps {
        sh '''
          set -euxo pipefail
          python3 -V
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -U pip wheel
          pip install -r requirements.txt
        '''
      }
    }

    stage('Playwright Browsers') {
      when {
        expression { params.MARKERS != 'api' } // skip if API-only
      }
      steps {
        sh '''
          set -euxo pipefail
          . .venv/bin/activate
          # Install browser binaries; avoid --with-deps (often needs sudo on CI)
          python -m playwright install chromium
        '''
      }
    }

    stage('Prepare .env') {
      steps {
        writeFile file: '.env', text: "TEST_ENV=${params.ENV}\n"
        sh 'echo "Using TEST_ENV=${TEST_ENV}"'
      }
    }

    stage('Run Tests') {
      steps {
        script {
          def browserPathArg = params.BROWSER_PATH?.trim() ? "--browser-path=${params.BROWSER_PATH.trim()}" : ""
          def headedArg = params.HEADED ? "--headed" : ""
          def markers   = params.MARKERS == 'all' ? '' : "-m ${params.MARKERS}"

          sh """
            set -euxo pipefail
            . .venv/bin/activate
            pytest ${markers} -n ${params.WORKERS} --dist=worksteal \\
              --clean-alluredir --alluredir=reports/allure-results \\
              --env=${params.ENV} ${headedArg} ${browserPathArg} -ra
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
      echo 'Build finished.'
      // cleanWs() // uncomment if you want smaller workspace
    }
    failure {
      echo 'Tests failed.'
    }
  }
}



// Use the official Playwright Python Docker image (most robust on CI)
// This avoids system dependency headaches and comes with browsers preinstalled.
// pipeline {
//   agent {
//     docker {
//       image 'mcr.microsoft.com/playwright/python:v1.47.1-jammy'
//       args '-u root:root -v $WORKSPACE:$WORKSPACE -w $WORKSPACE' // run as root if you need to write cache
//     }
//   }

//   options {
//     timestamps()
//     ansiColor('xterm')
//     skipDefaultCheckout(false)
//   }

//   parameters {
//     choice(name: 'MARKERS', choices: ['authentication', 'api', 'ui', 'e2e', 'smoke', 'regression', 'all'], description: 'Pytest -m marker to run')
//     string(name: 'ENV', defaultValue: 'dev', description: 'TEST_ENV / settings environment')
//     string(name: 'WORKERS', defaultValue: 'auto', description: 'xdist workers (e.g. 4 or auto)')
//     booleanParam(name: 'HEADED', defaultValue: false, description: 'Run browser headed (UI)')
//     choice(name: 'ALLURE_ATTACH', choices: ['json', 'png', 'both', 'none'], description: 'What to attach to Allure for API steps')
//   }

//   environment {
//     PIP_DISABLE_PIP_VERSION_CHECK = '1'
//     PYTHONDONTWRITEBYTECODE = '1'
//     TEST_ENV = "${params.ENV}"
//     ALLURE_API_ATTACH = "${params.ALLURE_ATTACH}"
//   }

//   stages {
//     stage('Checkout') {
//       steps { checkout scm }
//     }

//     stage('Python Setup') {
//       steps {
//         sh '''
//           set -euxo pipefail
//           python -V
//           python -m venv .venv
//           . .venv/bin/activate
//           pip install -U pip wheel
//           pip install -r requirements.txt
//         '''
//       }
//     }

//     // No browser install needed: image already has them

//     stage('Prepare .env') {
//       steps {
//         writeFile file: '.env', text: "TEST_ENV=${params.ENV}\n"
//         sh 'echo "Using TEST_ENV=${TEST_ENV}"'
//       }
//     }

//     stage('Run Tests') {
//       steps {
//         script {
//           def headedArg = params.HEADED ? "--headed" : ""
//           def markers   = params.MARKERS == 'all' ? '' : "-m ${params.MARKERS}"

//           sh """
//             set -euxo pipefail
//             . .venv/bin/activate
//             pytest ${markers} -n ${params.WORKERS} --dist=worksteal \\
//               --clean-alluredir --alluredir=reports/allure-results \\
//               --env=${params.ENV} ${headedArg} -ra
//           """
//         }
//       }
//     }

//     stage('Archive Reports') {
//       steps {
//         archiveArtifacts artifacts: 'reports/**/*', fingerprint: true, onlyIfSuccessful: false
//       }
//     }

//     stage('Publish Allure') {
//       steps {
//         allure includeProperties: false, jdk: '', results: [[path: 'reports/allure-results']]
//       }
//     }
//   }
// }

// Notes

// Your pytest-side report combiner writes a single reports/api-report.html and reports/api-report.json. The Jenkins “Archive Reports” step already grabs them, plus reports/workers/*.json.

// If you added CLI flags like --api-worker-html or --api-clean-workers, expose them as Jenkins params and append to the pytest command as needed.

// If your corp network blocks Playwright downloads, prefer the Docker image variant—it’s the most reliable on CI.