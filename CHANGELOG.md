# Changelog

## [1.8.1](https://github.com/CHIMEFRB/workflow/compare/v1.8.0...v1.8.1) (2024-07-16)


### Bug Fixes

* **daemon:** improved transfer daemon to handle config.archive updates ([0d4b4d6](https://github.com/CHIMEFRB/workflow/commit/0d4b4d6bd8c22a4bbec0f501fc3c6fa424c44414))

## [1.8.0](https://github.com/CHIMEFRB/workflow/compare/v1.7.0...v1.8.0) (2024-07-16)


### Features

* **validation-strategy:** added strict and relaxed validation modes ([3302b4c](https://github.com/CHIMEFRB/workflow/commit/3302b4caa4e28ce057d1678169884906d7b69e95))


### Bug Fixes

* **execute.py:** fixing command execution ([#84](https://github.com/CHIMEFRB/workflow/issues/84)) ([f226528](https://github.com/CHIMEFRB/workflow/commit/f2265289238ae50e507a0e7c0e0c4742654bd738))

## [1.7.0](https://github.com/CHIMEFRB/workflow/compare/v1.6.0...v1.7.0) (2024-07-16)


### Features

* **daemon:** added reworked transfer daemon ([8528f45](https://github.com/CHIMEFRB/workflow/commit/8528f45ecb0c67594067d1941dd9f3010485a646))


### Bug Fixes

* **tx:** fixed startup errors ([07e3d67](https://github.com/CHIMEFRB/workflow/commit/07e3d67b4ea22b7c72d18bae6dcf1fd67adb7e8f))

## [1.6.0](https://github.com/CHIMEFRB/workflow/compare/v1.5.0...v1.6.0) (2024-07-04)


### Features

* **argsource:** added a new runtime cli parameter to perform function based work, by passing the work obj itself to the func ([11adc37](https://github.com/CHIMEFRB/workflow/commit/11adc374151dfb9949b4215e471e60c14fb3a907))

## [1.5.0](https://github.com/CHIMEFRB/workflow/compare/v1.4.0...v1.5.0) (2024-07-04)


### Features

* **audit:** added an audit daemon to the workflow cli ([b73287a](https://github.com/CHIMEFRB/workflow/commit/b73287a9a8d23c07472b933731463ce887e1b954))
* **audit:** added tests ([e2f0be0](https://github.com/CHIMEFRB/workflow/commit/e2f0be084f832cb56cc70fc08995be2e13433b64))
* **execute:** added functionality to execute work with the work object as arguments ([b9927f5](https://github.com/CHIMEFRB/workflow/commit/b9927f5e9f921d0f95de50f4a88ab7bc0aa1c49f))
* **pypi:** added functionality to push to pypi as workflow.core ([fc811d5](https://github.com/CHIMEFRB/workflow/commit/fc811d575d69c4edcc63519491d8a17dee6de8c1))

## [1.4.0](https://github.com/CHIMEFRB/workflow/compare/v1.3.2...v1.4.0) (2024-06-29)


### Features

* **gha:** added ghcr container push ([f78275e](https://github.com/CHIMEFRB/workflow/commit/f78275e9a9c1275d090f955718185022441f7931))

## [1.3.2](https://github.com/CHIMEFRB/workflow/compare/v1.3.1...v1.3.2) (2024-06-29)


### Bug Fixes

* **execute:** properly handle cli options which are flags, i.e. --verbose ([ae3da80](https://github.com/CHIMEFRB/workflow/commit/ae3da8013241a4924fdcc5538e4c886b4e87f2cf))

## [1.3.1](https://github.com/CHIMEFRB/workflow/compare/v1.3.0...v1.3.1) (2024-06-26)


### Bug Fixes

* **execute:** executing a command no longer tries to evaluate the stdout to python types ([61e4ca3](https://github.com/CHIMEFRB/workflow/commit/61e4ca3e24573d0858d514554a57bb4493c059fd))

## [1.3.0](https://github.com/CHIMEFRB/workflow/compare/v1.2.2...v1.3.0) (2024-06-26)


### Features

* **helpers:** added a new category of workflow functions called helpers to provide common utililites in the pipelines framework ([bb3659b](https://github.com/CHIMEFRB/workflow/commit/bb3659b79ba5a93a43f48bf2b5d87fd0372a56c5))

## [1.2.2](https://github.com/CHIMEFRB/workflow/compare/v1.2.1...v1.2.2) (2024-06-26)


### Bug Fixes

* **deps:** removed mergedeep usage when collating results ([3104c80](https://github.com/CHIMEFRB/workflow/commit/3104c807ba4f4cb31b2df0cd005f756d92d857d4))

## [1.2.1](https://github.com/CHIMEFRB/workflow/compare/v1.2.0...v1.2.1) (2024-06-25)


### Bug Fixes

* **cli:** default options which are none, are no longer passed to cli ([bcb0cbb](https://github.com/CHIMEFRB/workflow/commit/bcb0cbbc77fcc7566db99d62772bf8c5c732d706))
* **cli:** run command now properly parses click cli argument names. ([26aceaf](https://github.com/CHIMEFRB/workflow/commit/26aceafa5b1fef8d6ee312711311f87b0dc1eceb))
* **execution:** fixed edge case in work execution due to json serializable error ([cb9ce26](https://github.com/CHIMEFRB/workflow/commit/cb9ce26972c8e1cc6daa41f24b75d5057c2776ef))
* **execution:** fixed issue when translating single and multiple letter click cli options to to code ([f67b1f7](https://github.com/CHIMEFRB/workflow/commit/f67b1f7f2848f652b237515622711a5ca486692b))

## [1.2.0](https://github.com/CHIMEFRB/workflow/compare/v1.1.0...v1.2.0) (2024-06-25)


### Features

* **cli/configs.py:** adding validation for deployments ([#67](https://github.com/CHIMEFRB/workflow/issues/67)) ([1154568](https://github.com/CHIMEFRB/workflow/commit/1154568351a3a2d13b8439ef4bfd82281147bd21))
* **cli:** improved the cli run command significantly ([894fd08](https://github.com/CHIMEFRB/workflow/commit/894fd080d4c4a13f2545aaaa20e1362c8f843eb9))


### Bug Fixes

* **cleanup:** tutorial ([53e7008](https://github.com/CHIMEFRB/workflow/commit/53e700835cf868cdc26999f9dc75357f6a5b92c7))
* **cli:** fixing ls and ps functions not receiving the right datatype for query and projection ([#64](https://github.com/CHIMEFRB/workflow/issues/64)) ([87767cb](https://github.com/CHIMEFRB/workflow/commit/87767cb674a3d72639d00e8b1b990c7cc5f48348))
* **imports:** fixed typings imports error ([98edf99](https://github.com/CHIMEFRB/workflow/commit/98edf99814a348a72add48ca54ee6ba0fb5e6dd9))
* **lifecycle:** fixed issue when running click cli wrapped functions were not reporting results,prods & plots properly ([769cb73](https://github.com/CHIMEFRB/workflow/commit/769cb735eebcead024136222a86b82ee3635491b))

## [1.1.0](https://github.com/CHIMEFRB/workflow/compare/v1.0.1...v1.1.0) (2024-06-18)


### Miscellaneous Chores

* release 1.1.0 ([65098ae](https://github.com/CHIMEFRB/workflow/commit/65098aecd54ce07dadcf04b353b76c2e91edc7da))

## [1.0.1](https://github.com/CHIMEFRB/workflow/compare/v1.0.0...v1.0.1) (2024-06-18)


### Bug Fixes

* **cli:** workspace set fix when passing path ([2d9ab04](https://github.com/CHIMEFRB/workflow/commit/2d9ab04ae909bf8587bbb9c49d752dff2d38e7ae))
* **json-schema:** added default mode as serialization ([5587cf7](https://github.com/CHIMEFRB/workflow/commit/5587cf719244aec470b538778fe27dc111c2715a))


### Documentation

* **readme:** added readme, moved docs to workflow-docs repo, consolidated test configs to pyproject ([20ba2b2](https://github.com/CHIMEFRB/workflow/commit/20ba2b20dc076cf3b92a51552c635daa63fbf14e))
* **readme:** formatting ([3681bd1](https://github.com/CHIMEFRB/workflow/commit/3681bd192cbda256d234ad04adc426f8d8678644))
* **readme:** update ([06f9a45](https://github.com/CHIMEFRB/workflow/commit/06f9a45253f633ee03d8ba0468af9eac23be3e11))

## [1.0.0](https://github.com/CHIMEFRB/workflow/compare/v0.10.0...v1.0.0) (2024-06-18)


### ⚠ BREAKING CHANGES

* **http:** work object by default only instantiates a buckets connection in the http context
* **workspace:** this change marks a departure from multiple config files and assumed that default workspace is always set

### Features

* **http:** httpcontext now supports requesting individual backends ([569d502](https://github.com/CHIMEFRB/workflow/commit/569d50205a1466627ad712a7c13db50860e8afe4))
* **workspace:** consolidated all workflow settings under single workspace file ([3f616ab](https://github.com/CHIMEFRB/workflow/commit/3f616aba86fedddcf5cb04524a8cce5b3b23dc16))


### Bug Fixes

* **http:** removed the clients dependency read workspace ([afd2273](https://github.com/CHIMEFRB/workflow/commit/afd227302263816f83bcab47487f2e12d2ff6c47))
* **utils:** reading workspace from a url now properly works ([ac6f890](https://github.com/CHIMEFRB/workflow/commit/ac6f8909bd6d0441978c0a592581a9f83af94ca6))
* **workspace:** fixed spelling error ([a52c9ca](https://github.com/CHIMEFRB/workflow/commit/a52c9caaedaf092f964fff1b5cb88733832207ab))
* **workspace:** fixed urls for dev workspace ([e789499](https://github.com/CHIMEFRB/workflow/commit/e789499a3efd745113255a49d5a2a6a883005826))
* **work:** work now attemps to reuse http context ([7df33e4](https://github.com/CHIMEFRB/workflow/commit/7df33e4b9a46cbde2dff8cb26e0e14673222b21f))

## [0.10.0](https://github.com/CHIMEFRB/workflow/compare/v0.9.1...v0.10.0) (2024-06-13)


### Features

* **client:** the http client now accepts either a str | List[str] as argument for baseurls ([460a731](https://github.com/CHIMEFRB/workflow/commit/460a73191d0349c9d05dc6409917a7161cb25f9e))


### Bug Fixes

* **github-actions:** fix for tests ([80f8b26](https://github.com/CHIMEFRB/workflow/commit/80f8b2627b0a85a532dc2f4b6658b677072b0044))

## [0.9.1](https://github.com/CHIMEFRB/workflow/compare/v0.9.0...v0.9.1) (2024-06-12)


### Bug Fixes

* **run.py:** fixing error when runspace is provided ([#54](https://github.com/CHIMEFRB/workflow/issues/54)) ([2a0f262](https://github.com/CHIMEFRB/workflow/commit/2a0f262ceea64b7084ff621ffbc1d784f6fa1a1b))

## [0.9.0](https://github.com/CHIMEFRB/workflow/compare/v0.8.2...v0.9.0) (2024-06-12)


### Features

* **github-actions:** added deployment action to publish docker containers ([1c5d71c](https://github.com/CHIMEFRB/workflow/commit/1c5d71c5cbe79147c4ab0f3d76e6a21e71aa7042))
* **results:** added workflow results API & CLI ([0d20eaf](https://github.com/CHIMEFRB/workflow/commit/0d20eafb5a4969af69b488c6458393de79123210))
* **workflow:** updates to tests, and general api cleanup ([644a744](https://github.com/CHIMEFRB/workflow/commit/644a744bea3173afb629c3dc1e7ad20c7325d645))


### Bug Fixes

* **dockerfile:** fixes ([cdf4004](https://github.com/CHIMEFRB/workflow/commit/cdf40048733ee44de83fbf83b1049159209ce254))
* **github-actions:** added debug ssh session ([bce85d6](https://github.com/CHIMEFRB/workflow/commit/bce85d653ecba20ca71e219df3bc29e4d440a3b3))

## [0.8.2](https://github.com/CHIMEFRB/workflow/compare/v0.8.1...v0.8.2) (2024-06-07)


### Bug Fixes

* **release-please:** fixes for release please config linting ([b285de4](https://github.com/CHIMEFRB/workflow/commit/b285de472420495fab062afd54db3f4dea229620))

## [0.8.1](https://github.com/CHIMEFRB/workflow/compare/v0.8.0...v0.8.1) (2024-06-07)


### Bug Fixes

* **release:** fixed the release-please action config ([eb0411c](https://github.com/CHIMEFRB/workflow/commit/eb0411c1c75fcdd360be80e408f5457455a76c85))

## [0.8.0](https://github.com/CHIMEFRB/workflow/compare/v0.7.0...v0.8.0) (2024-06-07)


### Features

* **python:** working build for py38,py39,py310 ([6c0b3ef](https://github.com/CHIMEFRB/workflow/commit/6c0b3ef00417eb4b72bb5067bb597c3b7b305ae4))

## [0.7.0](https://github.com/CHIMEFRB/workflow/compare/v0.6.0...v0.7.0) (2024-06-06)


### Features

* **cli:** multiple buckets + runspace ([#47](https://github.com/CHIMEFRB/workflow/issues/47)) ([817e125](https://github.com/CHIMEFRB/workflow/commit/817e125aa23911f75563cdf4a1fe4d858b37d55e))

## [0.6.0](https://github.com/CHIMEFRB/workflow/compare/v0.5.0...v0.6.0) (2024-06-04)


### Features

* **cli:** added buckets cli ([de14f28](https://github.com/CHIMEFRB/workflow/commit/de14f2841fb9f7f17c8c20240718af8bbe609055))

## [0.5.0](https://github.com/CHIMEFRB/workflow/compare/v0.4.0...v0.5.0) (2024-06-04)


### Features

* **dockerfile:** improvements to the workflow docker container ([af472b9](https://github.com/CHIMEFRB/workflow/commit/af472b98cbc3a2b7284221b2fe29e13f2c1c22af))


### Bug Fixes

* **archive:** check that basepath, mount in config, exists before continuing ([#39](https://github.com/CHIMEFRB/workflow/issues/39)) ([87fe370](https://github.com/CHIMEFRB/workflow/commit/87fe37096062da0761341e3a87c14af12a90c3b9))
* **cli:** improved cli structure ([08ce5e3](https://github.com/CHIMEFRB/workflow/commit/08ce5e32cd08e6eecfd62dcb0b51dbdee4a6b8cc))

## [0.4.0](https://github.com/CHIMEFRB/workflow/compare/v0.3.0...v0.4.0) (2024-05-28)


### Features

* add schedule cli ([#25](https://github.com/CHIMEFRB/workflow/issues/25)) ([56dcd6e](https://github.com/CHIMEFRB/workflow/commit/56dcd6e8f53853234de069bac4c77255c448cceb))
* **cli/main.py:** adding logging on top level function ([#37](https://github.com/CHIMEFRB/workflow/issues/37)) ([7820c62](https://github.com/CHIMEFRB/workflow/commit/7820c623406f582e7fceef22785cb040d1be04b3))
* **docker-compose-tutorial.yml:** adding docker compose for tutorial ([#35](https://github.com/CHIMEFRB/workflow/issues/35)) ([7b17e2a](https://github.com/CHIMEFRB/workflow/commit/7b17e2a987e09d8a950d9b4202b29c068321971f))

## [0.3.0](https://github.com/CHIMEFRB/workflow/compare/v0.2.0...v0.3.0) (2024-03-06)


### Features

* **examples:** added a dedicated examples folder ([908de1a](https://github.com/CHIMEFRB/workflow/commit/908de1a04a8fee12dfd40a3bfe5f1877dade1177))


### Bug Fixes

* **context.py:** fixing class validator ([#17](https://github.com/CHIMEFRB/workflow/issues/17)) ([7bc52bb](https://github.com/CHIMEFRB/workflow/commit/7bc52bb7a21fb55e0662fa5a819ace8d440bf4a6))
* **validate:** updated the function/command validation logic to support Windows ([3458f0b](https://github.com/CHIMEFRB/workflow/commit/3458f0b9046208344ba6ec6433f09f094ebe2a05))
* **work.py:** changes in validation ([#21](https://github.com/CHIMEFRB/workflow/issues/21)) ([af96307](https://github.com/CHIMEFRB/workflow/commit/af9630703394d725465ac330f06740586ffa76a3))
* **workspace:** improved the workspace set/unset logic ([d8f6802](https://github.com/CHIMEFRB/workflow/commit/d8f6802066a4a194cfea17bbad8964b0f392f065))

## [0.2.0](https://github.com/CHIMEFRB/workflow/compare/v0.1.0...v0.2.0) (2024-01-28)


### Features

* **workflow:** major refactor of core work to support multiple projects ([1fdd115](https://github.com/CHIMEFRB/workflow/commit/1fdd115df83355e42070b11baf90bf391a08b79c))


### Bug Fixes

* **ci:** fixed ci to run on pre ([bd67d17](https://github.com/CHIMEFRB/workflow/commit/bd67d173c36508df033beb08e42f11fa7ae1ad90))

## 0.1.0 (2023-07-19)


### ⚠ BREAKING CHANGES

* **workflow:** In addition to work.pipeline, work.site and work.user are now required parameters. Dropped support for site name allenby and deprecated attributes.
* **workflow:** breaking changes to workflow work object with the following move, precursors -> config.parent, groups -> config.orgs|config.teams, path is deprecated and archive is now moved to config.archive.

### Features

* **audit daemon:** add time buffer to deleting failed work ([46eb8f5](https://github.com/CHIMEFRB/workflow/commit/46eb8f54d9bed759307641afa8093a00e7c65aea))
* **audit daemon:** remove deletion from audit daemon scope ([bba327d](https://github.com/CHIMEFRB/workflow/commit/bba327d63a98496e3f077d9e1e02faf5d6e613ae))
* **cd:** added cd pipeline ([38b8b91](https://github.com/CHIMEFRB/workflow/commit/38b8b91d97151e321955b80f688d4c6a95dd0c76))
* **ci:** added pre-commit & tests ([80871a1](https://github.com/CHIMEFRB/workflow/commit/80871a1cb346f7acd62b121de8246bdc80e5f6c2))
* **cli:** added workflow pipelines cli ([8bf7515](https://github.com/CHIMEFRB/workflow/commit/8bf75157180a004d9bb9175d38d8494161ff990d))
* **copy-util:** created copy util ([271123c](https://github.com/CHIMEFRB/workflow/commit/271123c37259fa3b5376faaa745846cabff3628a))
* **results:** implement transfer daemon ([09456ca](https://github.com/CHIMEFRB/workflow/commit/09456caa2cd4e2c40936d36e282822118004deab))
* **tasks:** Updated tasks and tests to work with v2 buckets ([9662fd2](https://github.com/CHIMEFRB/workflow/commit/9662fd2a744660fb892e8939fb77d37b080c97d8))
* **transfer daemon:** handle failed and stale work deletion ([a69e19a](https://github.com/CHIMEFRB/workflow/commit/a69e19a4380fac828d937200864ea015f9559559))
* **transfer daemon:** return dict results instead of bool ([b5fc513](https://github.com/CHIMEFRB/workflow/commit/b5fc5136d020b479cebbf67dae9948c48f06137f))
* **transfer_daemon:** handle 400 Bad Request ([613d62b](https://github.com/CHIMEFRB/workflow/commit/613d62b97a26f429b7b3d800b9ab5adcf6f4fedc))
* **transfer_daemon:** update transfer rules ([b3e055b](https://github.com/CHIMEFRB/workflow/commit/b3e055be76a6b2f36c764d18d43b097227e04ad2))
* **workflow_daemons:** allow test_mode; fix tests ([37380e2](https://github.com/CHIMEFRB/workflow/commit/37380e24ae9007fdc33d572cd9e29692647b80d3))
* **workflow-daemons:** add cli options; continuously run daemons ([f2f0930](https://github.com/CHIMEFRB/workflow/commit/f2f09308dec9f35f899a4c0ef6593856966e25fb))
* **workflow-pipelines:** added cli support ([84583e0](https://github.com/CHIMEFRB/workflow/commit/84583e02a9d2bfa781332158eea233dc86376141))
* **workflow-piplines:** added deploy and rm commands ([3ec10c4](https://github.com/CHIMEFRB/workflow/commit/3ec10c46539fbbe5d0a74f2d0620d9eaba0998d7))
* **workflow/buckets:** added functionality to return ids when depositing work ([f831b15](https://github.com/CHIMEFRB/workflow/commit/f831b1553d5c70f52061d3c4e3bd62e220648b21))
* **workflow:** add functionality for work.config.archive ([4d595f7](https://github.com/CHIMEFRB/workflow/commit/4d595f7d4771f8123e3027704d7cd206dd0b6c94))
* **workflow:** added capability to filter workflow run by work.tags and work.config.parent fields ([3ec1043](https://github.com/CHIMEFRB/workflow/commit/3ec10438950fae499897a29f0f8adb957edc39eb))
* **workflow:** Added HTTP interface to the work object ([645103a](https://github.com/CHIMEFRB/workflow/commit/645103a411907a63fb87a9884c75106605542026))
* **workflow:** added pre-commit, gitignore configs. Reorganized project structure. Starting work on developing resources structure for results/buckets API ([05a00c2](https://github.com/CHIMEFRB/workflow/commit/05a00c26e48667252d87b5509526d65a6f6c50d4))
* **workflow:** added support for work.functiona and work.command ([400e29e](https://github.com/CHIMEFRB/workflow/commit/400e29e8ab864589c57428853e9805e108df419c))
* **workflow:** added support for work.notify.slack functionality ([0a0f569](https://github.com/CHIMEFRB/workflow/commit/0a0f5697cbc7dbb7fc6802751923d8283a8dea8e))
* **workflow:** added utility to check if the script is running from k8s or docker runtime ([193ee01](https://github.com/CHIMEFRB/workflow/commit/193ee016e2caf25f983146ff33bd641aac739130))
* **workflow:** added view to cli ([56810e8](https://github.com/CHIMEFRB/workflow/commit/56810e835f6d4d52059f6a4f6dd0878c175c29d4))
* **workflow:** cli ([0a4396f](https://github.com/CHIMEFRB/workflow/commit/0a4396f2c331c263c1dbebe1e62d1ad7591c4dff))
* **workflow:** First crack at audit daemon ([40d04ab](https://github.com/CHIMEFRB/workflow/commit/40d04abdf4847b8309ea7919f5da3c3d9dc40f46))
* **workflow:** First crack at transfer daemon rough code. ([f84316b](https://github.com/CHIMEFRB/workflow/commit/f84316bb424fc05b083f88dc5217fcc74abfcd83))
* **workflow:** Made audit daemon runnable ([68e19c3](https://github.com/CHIMEFRB/workflow/commit/68e19c378ea67342e48ff4046106c7625baf7f05))
* **workflow:** major qol improvement for work object ([1fa93d2](https://github.com/CHIMEFRB/workflow/commit/1fa93d24defd09bcad966213ebc096a403e75e36))
* **workflow:** refactored entire workflow core ([f77df8f](https://github.com/CHIMEFRB/workflow/commit/f77df8f281469882760d3c577775248b11e2453a))
* **workflow:** run: upload logs to loki ([42b2709](https://github.com/CHIMEFRB/workflow/commit/42b27094624bd37bf675ed47903597c9732cdfca))
* **workflow:** site names ([eb8985d](https://github.com/CHIMEFRB/workflow/commit/eb8985da9263e1aeb32eb5622b15b8d5967550c3))
* **workflow:** updated to workflow cli to handler merging of defaults and output of function more gracefullu ([857fe38](https://github.com/CHIMEFRB/workflow/commit/857fe381b4c1a9d175ae267de22166e48980c6ad))
* **workflow:** updated work object ([c89822c](https://github.com/CHIMEFRB/workflow/commit/c89822c382952e6aaedb0c2eddfd3e731e124f17))
* **workflow:** work.withdraw now supports selecting work on event, site, priority and user in addition to pipeline ([cda6ade](https://github.com/CHIMEFRB/workflow/commit/cda6ade473ee0a1e2f33af467dcfce83e58cb66d))


### Bug Fixes

* add aro as valid site ([d60ada7](https://github.com/CHIMEFRB/workflow/commit/d60ada70834b4ce88778e9e3744fbc113f143558))
* **archive-run:** check for files before creating directory ([e24886d](https://github.com/CHIMEFRB/workflow/commit/e24886d4cc5f9df4c08ebcacb435a37e7057ecb9))
* **buckets:** added cli to delete works ([c72c61d](https://github.com/CHIMEFRB/workflow/commit/c72c61d93e341f15b563fe88b5ffff33e06c38d5))
* **configs:** added base structure ([3382816](https://github.com/CHIMEFRB/workflow/commit/33828163a7f0a7e4a25889470f523222398ce89a))
* **logging:** fixed issue when log level was not propogated to root handlers ([8f5e529](https://github.com/CHIMEFRB/workflow/commit/8f5e529e2de15070b0b1846369161a70e415b29d))
* **modules:** fixed results default urls ([97a388d](https://github.com/CHIMEFRB/workflow/commit/97a388d00caa9c280fc2495951eb5685e813e0e2))
* **notify:** append to instead of overwriting ([6d70fcb](https://github.com/CHIMEFRB/workflow/commit/6d70fcb9541adefe856d2978ba1f1327f5a49d74))
* **notify:** append to instead of overwriting ([6ca4a74](https://github.com/CHIMEFRB/workflow/commit/6ca4a74e7e0c20e4d3ef83818acebdb13a488c38))
* **pipeline:** fixed errors handling null work.parameters and tests ([b549aa7](https://github.com/CHIMEFRB/workflow/commit/b549aa71daa379ec4dab7cb23eebc4c04f5023e7))
* **pipelines:** import fix ([85b28cc](https://github.com/CHIMEFRB/workflow/commit/85b28ccfb5ca98eb703c6317bca213e1b9977e5e))
* **pre-commit:** significant pre-commit fixes ([e5e5836](https://github.com/CHIMEFRB/workflow/commit/e5e5836f6feda1ce55aa5796e6004107a795dad9))
* **readme:** added basic readme ([e10b06f](https://github.com/CHIMEFRB/workflow/commit/e10b06fb2fe9ee1c6f721cc3054b1ecfc1e6feb5))
* **results:** update return values to int ([d2081df](https://github.com/CHIMEFRB/workflow/commit/d2081dfb75ae19e77b8784db23f083c41a4508f3))
* **slack-notifications:** format products and plots into slack hyperlinks ([1c4f40a](https://github.com/CHIMEFRB/workflow/commit/1c4f40adc7855a1f1217a7fc0f054dbd158ccc17))
* **transfer daemon:** fix deposit result status ([314f36c](https://github.com/CHIMEFRB/workflow/commit/314f36cb7d63a9600de1d887c2f382e53ec82a1f))
* **transfer daemon:** fix typo ([951ad88](https://github.com/CHIMEFRB/workflow/commit/951ad88d8ac0f8dd3329fa18e11ec08fd2015a94))
* **transfer daemon:** Updated transfer daemon to work with results ([d7ee97e](https://github.com/CHIMEFRB/workflow/commit/d7ee97e07052ecdef167a19ee9db7532f0eb6a47))
* **transfer_daemon:** fix Bad Request bug in 104 ([5a217e4](https://github.com/CHIMEFRB/workflow/commit/5a217e4f0d271650ee1d90253bcc15dffe38005b))
* **transfer_daemon:** fix bug when no results should be deposited ([c843470](https://github.com/CHIMEFRB/workflow/commit/c843470c261ebd8300fa0051a0a7f8fe30f49bf9))
* **transfer_daemon:** max limit_per_run adjusted to OId length ([64db691](https://github.com/CHIMEFRB/workflow/commit/64db6917642627563af9e71ce5b7dcc63d40a0c4))
* **transfer-daemon:** update archive keys ([1f3cbdf](https://github.com/CHIMEFRB/workflow/commit/1f3cbdf630b8c5ca16f74cf8bfb17aa37bf23667))
* **various:** fixes for lint, dockerfile and flake8 ([d375a0e](https://github.com/CHIMEFRB/workflow/commit/d375a0ea19b0cf4e67745a0662cc2c8e35c98163))
* **work.py:** fixed condition statement for pipeline reformatting ([067db77](https://github.com/CHIMEFRB/workflow/commit/067db775ed32ab75bcfbaadcaae63865d1ecfaae))
* **work:** added pipeline name reformatting ([b3f791b](https://github.com/CHIMEFRB/workflow/commit/b3f791b492c3e004956d9acdc4a7097ee8702305))
* **work:** added syntax warning for bad pipeline name ([1233e59](https://github.com/CHIMEFRB/workflow/commit/1233e59609db7743c05ea2b64d8392bc73d51e6f))
* **workflow pipeline:** buckets run on 8004 onsite, not 8001 ([922a84a](https://github.com/CHIMEFRB/workflow/commit/922a84ab99182c37e4b274c635d2bea9f57bf4a8))
* **workflow_daemons:** fix args that were passed incorrectly ([9ca093f](https://github.com/CHIMEFRB/workflow/commit/9ca093f16ff91f957b54da95d65c2778bf8ad279))
* **workflow_daemons:** fix tests ([86e2573](https://github.com/CHIMEFRB/workflow/commit/86e25730ec033a4d6a4ff596778df8dec80527c5))
* **workflow-cli:** better output for work lifecycle ([33f435e](https://github.com/CHIMEFRB/workflow/commit/33f435ed27855201cf7b4445bd83b18748b4e471))
* **workflow-cli:** removed empty status field ([d4d42b8](https://github.com/CHIMEFRB/workflow/commit/d4d42b8daa9a6b9f38319589af1b3ea8061cb8ee))
* **workflow:** added [@retry](https://github.com/retry) to work.delete ([c7b14f8](https://github.com/CHIMEFRB/workflow/commit/c7b14f83745c7ff8e79a46c1769468256492dea2))
* **workflow:** added loki logging format ([11fb580](https://github.com/CHIMEFRB/workflow/commit/11fb5804da0e0a4c6c26d58755b132376017589c))
* **workflow:** added loki logging handler for chime jobs ([36666a4](https://github.com/CHIMEFRB/workflow/commit/36666a447187983befa3e298c25e4b29e343a814))
* **workflow:** added retry for updates in cli ([811b820](https://github.com/CHIMEFRB/workflow/commit/811b8202ce710442c3e4ea5305d43df12d092181))
* **workflow:** better cli display ([eb174cf](https://github.com/CHIMEFRB/workflow/commit/eb174cf4a6fb6c5c689358052e5d2100234fda37))
* **workflow:** changed default attempts from 1-&gt;0, the buckets system auto-increments attempt when work is withdrawn ([c75f50f](https://github.com/CHIMEFRB/workflow/commit/c75f50f16d48f68f413aad1a69985b1baa85f1d0))
* **workflow:** changed workflow buckets prune -&gt; workflow buckets rm ([5ea31f4](https://github.com/CHIMEFRB/workflow/commit/5ea31f4737a8294f8988e1000142ac2d53710c93))
* **workflow:** changed workflow run to not use process call ([465d2b3](https://github.com/CHIMEFRB/workflow/commit/465d2b380afea00e2d6f27c77734dc5268671561))
* **workflow:** fixed duplicate logging issue ([a0b5a99](https://github.com/CHIMEFRB/workflow/commit/a0b5a992895e892c115a64d47d335be0a3fb166d))
* **workflow:** fixed stderr/stdout in workflow runner ([54f2510](https://github.com/CHIMEFRB/workflow/commit/54f2510fe096c35173814b5182d330d28e5c700e))
* **workflow:** improved exception catching ([72c6f64](https://github.com/CHIMEFRB/workflow/commit/72c6f64b1eceab89854baec1f3b19d9dc2812726))
* **workflow:** improved test coverage ([cf7cb3c](https://github.com/CHIMEFRB/workflow/commit/cf7cb3ca31d2725af032ac8f8fc32d9145899c69))
* **workflow:** improved workflow run cli functionality ([95ba604](https://github.com/CHIMEFRB/workflow/commit/95ba60455f36f8ba3eb0290f31645ee4a8b1f4fb))
* **workflow:** reduced complexity ([e263121](https://github.com/CHIMEFRB/workflow/commit/e263121db3243e4a5e7165ea4505e7af8e7adf3b))
* **workflow:** reorganized work ([17785c2](https://github.com/CHIMEFRB/workflow/commit/17785c2580ee7d66f9f08d1232d96ac907c84835))
* **workflow:** significated changes to the work object ([4ed2a38](https://github.com/CHIMEFRB/workflow/commit/4ed2a38d67173d29df87e1c83333c9d276b05ef2))
* **workflow:** transfer daemon, fixed issue with stale work ([db0e3bd](https://github.com/CHIMEFRB/workflow/commit/db0e3bdca4703f9be7b33ab0a8a6b51f6008f476))
* **workflow:** undeprecated config parameter to be used with pipelines ([cdd723c](https://github.com/CHIMEFRB/workflow/commit/cdd723c199819c68ca0ca8a9b2397105d497e1d5))
* **workflow:** updated cli ([92e5be3](https://github.com/CHIMEFRB/workflow/commit/92e5be30531f44a1036859d882e771c34962996b))
* **workflow:** updated workflow function execution to merge work.results recursively ([4b2207d](https://github.com/CHIMEFRB/workflow/commit/4b2207d77f647d37cfae57b89e1d81b9ced37848))
* **workflow:** updated workflow run cli ([cdcb970](https://github.com/CHIMEFRB/workflow/commit/cdcb9701ce200edd61b320930afb6a2f4d85bebb))
* **workflow:** work object updates ([1591198](https://github.com/CHIMEFRB/workflow/commit/1591198fb9fc876914b0d73dcd114d1af21e71c9))
* **workflow:** work object value attempt is defaulted to 1 if not provided ([fb8423b](https://github.com/CHIMEFRB/workflow/commit/fb8423b1f6eaebf7c03bbccc9c1101184f835b7a))
* **workflow:** work token: changed token to be a top level attr, work.config.token -&gt; work.token ([6d6322a](https://github.com/CHIMEFRB/workflow/commit/6d6322a3ae5256f0c69582d6b0a9dd67ec0fbd45))
* **workflow:** work.notify.slack.reply field added ([9234dc0](https://github.com/CHIMEFRB/workflow/commit/9234dc005c61dee80c81c47435784f7c747a6dd6))
* **workflow:** workflow run spinner now has a 1000x slowdown when detected to be running from a container to reducing log printing ([02ddd94](https://github.com/CHIMEFRB/workflow/commit/02ddd9406af766a685f1138d718a11d9fb71999d))


### Documentation

* **work:** fix typo ([68e534e](https://github.com/CHIMEFRB/workflow/commit/68e534eff77a8458273c1e7afb887d12bc9752e7))
* **workflow:** improved docstrings for workflow run command ([f96de64](https://github.com/CHIMEFRB/workflow/commit/f96de643f3d488016972ffc43fad89ca46d25ade))
* **workflow:** updated some docs ([f6d6899](https://github.com/CHIMEFRB/workflow/commit/f6d68999c0d0690572398186cf3e02d49e942375))
