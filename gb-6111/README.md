# 风栎琴作·管风琴维护卷复原

从整月维护卷择单归档，把关联琴体、维修工单和测记复原到隔离表，再用证据确认缺卷或传输损伤。

## 业务流程

1. 维修库卷宗
2. 复原范围
3. 归档演练
4. 复原证明

PostgreSQL 原生 COPY、外键依赖闭包和逐段 SHA-256 字节核验。

巡修组过去从整月表格复制工单，再手动补录琴体档案和测记。容易漏随工测记、误把同琴体未选工单一并交出，也缺少交接包损坏的判定记录。上游是巡修主管整理的维修卷，下游是赴馆复查的技术员和档案复核员。

09:00 打开 organ-ledger-2026-11.copy 对应的十一月维修卷。09:05 选 W-1131、W-1138。09:07 设置最多 20 张。09:10 提交演练。09:12 核对 2 个琴体、2 张工单、3 条测记。09:15 复核三个 COPY 摘要后导出证明。09:20 用损伤卷重跑，确认只输出阻断证据。

先按请求顺序取上限内的工单，把父琴体与其所有子测记一并选中。PostgreSQL COPY 以主键 C 排序流出 UTF-8 CSV，每段计算 SHA-256。全部段校验通过后才按外键顺序还原。校验报告重新导出目标表并对照原始段摘要。

范围为应用演练中的逻辑数据卷。以数据库隔离临时表核验，数据库事务结束后自动清除，不提供整库 DDL、角色、物理 WAL 或生产恢复编排。

## 启动

```sh
cp -n .env.example .env
docker compose config --quiet
docker compose up -d --build --wait
```

打开 <http://localhost:18312>。OpenAPI 在 <http://localhost:19312/docs>，数据库映射到本机 17812。所有暴露端口只绑定回环地址。Compose 启动 frontend、backend、worker、db、redis，各自通过健康探针检查。数据库、Redis 和共享产物目录各有命名卷；任务状态及导出内容以数据库中的证据为准。

首次启动时幂等载入演示数据。手动载入可运行 `docker compose exec -T backend python -m scripts.seed_demo`。常规停止可用 `docker compose down`。验收环境清理才加 `-v`，它会删除本项目的数据卷。

## 角色与交接

演示账号共用口令 `Demo-DbWorkbench-2026`。

| 登录名 | 角色 | 可执行操作 |
|---|---|---|
| operator | 资料操作员 | 登记业务资料、设置「本次最多复原工单数」、提交、查看和下载结果 |
| reviewer | 业务复核员 | 查看执行证据、签署单次复核、下载交接单 |
| viewer | 只读观察员 | 查看资料、执行结果及审计，下载证据 |

选用「organ-ledger-2026-11.copy」对应的演示资料，保存一份复演资料，再以默认参数 20 提交。worker 保存结果摘要、业务明细和 SHA-256。复核员登录后在「复原证明」签署。

## 开发说明

| 部分 | 实现 |
|---|---|
| 前端 | 原生 HTML、CSS、JavaScript ES Modules、Nginx |
| 后端 | Python 3.11、FastAPI、SQLAlchemy、JWT |
| 数据库 | PostgreSQL 16 |
| 后台执行 | Redis 通知、数据库持久任务队列和行锁、Python worker |

从 `backend/src/domain/scenario.py` 修改业务入口和演示口径，运行 `docker compose up -d --build --wait` 查看变更。数据库表结构在 `backend/src/models` 和 `backend/migrations`，输入模型在 `backend/src/schemas`。业务页和请求接口在 `frontend/src/pages`、`frontend/src/api`。资料、执行、复核三个工作流实体各有独立表和 API；场景输入及结果保留在所属资料和批次中。

角色枚举在 `backend/src/constants/roles.py`、`frontend/src/constants/roles.js`，用于服务端访问控制、账号初始化、前端导航与签署。批次状态在 `backend/src/constants/job_state.py`、`frontend/src/constants/states.js`，用于队列、状态 API、状态标记与轮询。登记、提交、完成和签署事件写入审计表。

`COMPOSE_PROJECT_NAME` 设置栈名，`FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 设置端口。通过 `DB_PASSWORD`、`JWT_SECRET`、`DEMO_PASSWORD` 配置本地凭据。设置 `SEED_DEMO=false` 可关闭演示数据载入，此时数据库初始没有演示账号。数据库密码调整后，已有数据卷需在数据库内同步修改用户密码。

## 验收范围

COPY 使用隔离临时表和应用层归档卷。覆盖数据恢复与依赖核验，整库 DDL、角色和 WAL 在范围之外。 当前界面用 JSON 编辑业务资料，以 JSON 下载证据。过程和截图保存在批次的 [验收记录](../../test-artifacts/gb-6111/TESTING.md)。

[MIT License](LICENSE)
