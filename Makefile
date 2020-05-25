export NAME?=whoisjs
export NAMESPACE?=whoisjs
export IMAGE?=matthewgall/whoisjs.com
export COLO:=$(shell kubectx -c)

.PHONY: apply
apply:
	@cat k8s.yml | envsubst | kubectl apply -n ${NAMESPACE} -f -
	@cat secrets.yml | envsubst | kubectl apply -n ${NAMESPACE} -f -

.PHONY: delete
delete:
	@cat k8s.yml | envsubst | kubectl delete -n ${NAMESPACE} -f -
	@cat secrets.yml | envsubst | kubectl delete -n ${NAMESPACE} -f -

.PHONY: deploy
deploy:
	kubectl rollout restart deployment/${NAME} -n ${NAMESPACE} && kubectl rollout status deployment/${NAME} -n ${NAMESPACE}

.PHONY: redis-cli
redis-cli:
	redis-cli -u ${REDIS_URL}