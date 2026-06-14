pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'khairulwara25'
        IMAGE          = "khairulwara25/sentiment-api"
        APP_CTR        = 'sentiment_ci_app'
        CHROME_CTR     = 'sentiment_ci_chrome'
        CI_NET         = 'sentiment_ci_net'
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {

        stage('Fetch') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run') {
            steps {
                sh '''
                    set -e
                    docker network create ${CI_NET} || true
                    docker rm -f ${APP_CTR} || true
                    docker build -t ${IMAGE}:unstable .
                    docker run -d --name ${APP_CTR} --network ${CI_NET} ${IMAGE}:unstable
                    echo "Waiting for the unstable app to become healthy..."
                    for i in $(seq 1 40); do
                        if docker exec ${APP_CTR} python -c "import requests,sys; sys.exit(0 if requests.get('http://localhost:5000/health').status_code==200 else 1)" >/dev/null 2>&1; then
                            echo "App is healthy."; break
                        fi
                        sleep 3
                    done
                    docker exec ${APP_CTR} python -c "import requests; print(requests.get('http://localhost:5000/health').json())"
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    set -e
                    docker exec -e BASE_URL=http://localhost:5000 ${APP_CTR} python -m pytest tests/test_api.py -v
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                    set -e
                    docker rm -f ${CHROME_CTR} || true
                    docker run -d --name ${CHROME_CTR} --network ${CI_NET} --shm-size=2g selenium/standalone-chrome:latest
                    echo "Waiting for Selenium Chrome to be ready..."
                    for i in $(seq 1 40); do
                        if docker exec ${APP_CTR} python -c "import requests,sys; sys.exit(0 if requests.get('http://${CHROME_CTR}:4444/wd/hub/status').json().get('value',{}).get('ready') else 1)" >/dev/null 2>&1; then
                            echo "Selenium is ready."; break
                        fi
                        sleep 3
                    done
                    docker exec -e SELENIUM_REMOTE_URL=http://${CHROME_CTR}:4444 -e APP_URL=http://${APP_CTR}:5000 ${APP_CTR} python -m pytest tests/test_ui.py -v
                '''
            }
        }

        stage('Build and Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                        set -e
                        docker build -t ${IMAGE}:unstable .
                        docker build -t ${IMAGE}:stable ./stable-fallback
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push ${IMAGE}:unstable
                        docker push ${IMAGE}:stable
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    set -e
                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/blue-deployment.yaml
                    kubectl apply -f k8s/green-deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout restart deployment/sentiment-blue-deployment deployment/sentiment-green-deployment
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=240s
                    kubectl rollout status deployment/sentiment-green-deployment --timeout=240s
                    kubectl get pods,svc -o wide
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f ${APP_CTR} ${CHROME_CTR} || true
                docker network rm ${CI_NET} || true
            '''
        }
    }
}
