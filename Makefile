.PHONY: deploy
deploy:
	snowboard html -o docs/index.html -t docs/alpha.html -q snowboard.apib
	rsync -a --progress docs/index.html ${SSH_USER}@${SSH_HOST}:${SSH_PATH}

.PHONY: redis-cli
redis-cli:
	redis-cli -u ${REDIS_URL}