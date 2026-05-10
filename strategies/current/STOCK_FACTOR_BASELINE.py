#coding:gbk
import math


def init(C):
    C.accountid = "testS"
    C.period = "1d"
    C.lookback = 160
    C.rebalance_interval = 5
    C.target_num = 20
    C.max_pool_size = 900
    C.finance_pool_limit = 650
    C.max_single_weight = 0.050
    C.max_industry_weight = 0.200
    C.trade_threshold_shares = 100
    C.min_price = 3.0
    C.min_avg_amount = 25000000.0
    C.initial_cash = 1000000.0
    C.last_rebalance_bar = -999999

    C.target_position_bull = 0.88
    C.target_position_normal = 0.72
    C.target_position_weak = 0.38
    C.target_position_bear = 0.12

    C.finance_refresh_interval = 60
    C.finance_chunk_size = 80
    C.last_finance_bar = -999999
    C.finance_cache = {}
    C.finance_coverage = 0.0
    C.finance_disabled = False
    C.finance_error_count = 0

    C.ml_horizon = 20
    C.ml_min_samples = 260
    C.ml_blend = 0.16
    C.ml_pending = []
    C.ml_weights = {}
    C.ml_sample_count = 0
    C.ml_features = [
        "mom20_z", "mom60_z", "mom120_z", "rev5_z", "low_vol20_z",
        "low_vol60_z", "liquidity_z", "breakout_z", "trend_quality_z",
        "value_z", "quality_z", "growth_z", "turnover_z", "flow_z"
    ]

    C.stock_pool = _build_stock_pool(C)
    C.industry_map = _build_industry_map(C, C.stock_pool)
    C.benchmark = C.stockcode + "." + C.market
    universe = list(C.stock_pool)
    if C.benchmark not in universe:
        universe.append(C.benchmark)
    C.set_universe(universe)
    C.stage_stats = {}
    print("V4_INIT pool=%d industry_groups=%d benchmark=%s target_num=%d" %
          (len(C.stock_pool), len(set(C.industry_map.values())), C.benchmark, C.target_num))


def handlebar(C):
    if C.barpos < C.lookback:
        return
    if C.barpos - C.last_rebalance_bar < C.rebalance_interval:
        return
    C.last_rebalance_bar = C.barpos

    date = _date_str(C)
    close_map = C.get_history_data(C.lookback, C.period, "close")
    volume_map = C.get_history_data(C.lookback, C.period, "volume")
    high_map = C.get_history_data(60, C.period, "high")
    low_map = C.get_history_data(60, C.period, "low")
    amount_map = _safe_history(C, 25, "amount")

    market_state, target_position, market_mom60 = _market_state(C, close_map)
    rows = _build_candidate_rows(C, close_map, volume_map, high_map, low_map, amount_map)
    if not rows:
        print("%s V4_WARN no_valid_candidates" % date)
        return

    rows = sorted(rows, key=lambda r: r["rough_score"], reverse=True)[:C.max_pool_size]
    if C.barpos - C.last_finance_bar >= C.finance_refresh_interval:
        _refresh_financial_factors(C, rows[:C.finance_pool_limit], date)
        C.last_finance_bar = C.barpos

    _add_financial_features(C, rows)
    _standardize_and_score(C, rows)
    _update_ml_model(C, rows)
    _apply_ml_score(C, rows)

    ranked = sorted(rows, key=lambda r: r["score"], reverse=True)
    selected = _select_with_industry_cap(C, ranked, C.target_num)
    weights = _allocate_inverse_vol_weights(C, selected, target_position)
    _rebalance(C, date, weights, close_map)
    _update_stage_stats(C, date, market_state, target_position, len(rows), selected)

    selected_codes = ",".join([r["stock"] for r in selected])
    print("%s V4_SELECT state=%s valid=%d finance_cov=%.2f ml_n=%d target_pos=%.2f selected=%s" %
          (date, market_state, len(rows), C.finance_coverage, C.ml_sample_count, target_position, selected_codes))
    _paint(C, len(rows), target_position, market_mom60, len(selected), C.finance_coverage, C.ml_sample_count)


def _build_stock_pool(C):
    sectors = [
        "\u6caa\u6df1A\u80a1",
        "\u6caa\u6df1\u4eacA\u80a1",
        "A\u80a1"
    ]
    stocks = []
    for sector in sectors:
        try:
            stocks = C.get_stock_list_in_sector(sector)
        except Exception:
            stocks = []
        if stocks:
            break
    out = []
    seen = set()
    for stock in stocks:
        if not _is_a_share(stock):
            continue
        if stock in seen:
            continue
        seen.add(stock)
        out.append(stock)
    return out


def _build_industry_map(C, stock_pool):
    pool = set(stock_pool)
    industry_map = {}
    for industry in _industry_names():
        try:
            members = C.get_stock_list_in_sector(industry)
        except Exception:
            members = []
        for stock in members:
            if stock in pool and stock not in industry_map:
                industry_map[stock] = industry
    for stock in stock_pool:
        if stock not in industry_map:
            industry_map[stock] = _prefix_group(stock)
    return industry_map


def _industry_names():
    return [
        "\u519c\u6797\u7267\u6e14", "\u57fa\u7840\u5316\u5de5", "\u94a2\u94c1",
        "\u6709\u8272\u91d1\u5c5e", "\u7535\u5b50", "\u5bb6\u7528\u7535\u5668",
        "\u98df\u54c1\u996e\u6599", "\u7eba\u7ec7\u670d\u9970", "\u8f7b\u5de5\u5236\u9020",
        "\u533b\u836f\u751f\u7269", "\u516c\u7528\u4e8b\u4e1a", "\u4ea4\u901a\u8fd0\u8f93",
        "\u623f\u5730\u4ea7", "\u5546\u8d38\u96f6\u552e", "\u793e\u4f1a\u670d\u52a1",
        "\u7efc\u5408", "\u5efa\u7b51\u6750\u6599", "\u5efa\u7b51\u88c5\u9970",
        "\u7535\u529b\u8bbe\u5907", "\u56fd\u9632\u519b\u5de5", "\u8ba1\u7b97\u673a",
        "\u4f20\u5a92", "\u901a\u4fe1", "\u94f6\u884c", "\u975e\u94f6\u91d1\u878d",
        "\u6c7d\u8f66", "\u673a\u68b0\u8bbe\u5907", "\u7164\u70ad", "\u77f3\u6cb9\u77f3\u5316",
        "\u73af\u4fdd", "\u7f8e\u5bb9\u62a4\u7406"
    ]


def _safe_history(C, count, field):
    try:
        return C.get_history_data(count, C.period, field)
    except Exception:
        return {}


def _build_candidate_rows(C, close_map, volume_map, high_map, low_map, amount_map):
    rows = []
    for stock in C.stock_pool:
        prices = _series(close_map.get(stock, []))
        volumes = _series(volume_map.get(stock, []))
        if len(prices) < C.lookback or len(volumes) < 80:
            continue
        price = prices[-1]
        if price < C.min_price:
            continue
        if _is_dirty_stock(C, stock, prices, volumes):
            continue
        amounts = _series(amount_map.get(stock, []))
        avg_amount = _mean(amounts[-20:]) if amounts else price * _mean(volumes[-20:])
        if avg_amount < C.min_avg_amount:
            continue

        mom20 = _ret(prices, 20)
        mom60 = _ret(prices, 60)
        mom120 = _ret(prices, 120)
        rev5 = -_ret(prices, 5)
        vol20 = max(_return_std(prices[-21:]), 0.0001)
        vol60 = max(_return_std(prices[-61:]), 0.0001)
        low_vol20 = -vol20
        low_vol60 = -vol60
        liquidity = math.log(max(avg_amount, 1.0))
        breakout = _breakout_score(high_map, low_map, prices, stock)
        trend_quality = _trend_quality(prices[-60:])
        volume_ratio = _mean(volumes[-5:]) / max(_mean(volumes[-60:]), 1.0)
        flow = math.log(max(volume_ratio, 0.05))
        turnover = _turnover_proxy(avg_amount, price, volumes)
        rough = 0.32 * mom60 + 0.20 * mom120 + 0.15 * breakout + 0.12 * trend_quality
        rough += 0.08 * rev5 + 0.05 * flow - 0.08 * vol60
        rows.append({
            "stock": stock,
            "price": price,
            "industry": C.industry_map.get(stock, _prefix_group(stock)),
            "mom20": mom20,
            "mom60": mom60,
            "mom120": mom120,
            "rev5": rev5,
            "vol20": vol20,
            "vol60": vol60,
            "low_vol20": low_vol20,
            "low_vol60": low_vol60,
            "liquidity": liquidity,
            "breakout": breakout,
            "trend_quality": trend_quality,
            "turnover": turnover,
            "flow": flow,
            "rough_score": rough
        })
    return rows


def _is_dirty_stock(C, stock, prices, volumes):
    if prices[-1] <= 0 or volumes[-1] < 0:
        return True
    if _has_bad_gap(prices):
        return True
    if _is_limit_like(prices):
        return True
    try:
        name = C.get_stock_name(stock)
    except Exception:
        name = ""
    if name:
        up = str(name).upper()
        if "ST" in up or "\u9000" in str(name):
            return True
    try:
        if C.is_suspended_stock(stock):
            return True
    except Exception:
        pass
    if _mean(volumes[-20:]) <= 0:
        return True
    return False


def _has_bad_gap(prices):
    for i in range(max(1, len(prices) - 25), len(prices)):
        if prices[i - 1] <= 0 or prices[i] <= 0:
            return True
        r = prices[i] / prices[i - 1] - 1.0
        if abs(r) > 0.245:
            return True
    return False


def _is_limit_like(prices):
    if len(prices) < 2 or prices[-2] <= 0:
        return False
    r = prices[-1] / prices[-2] - 1.0
    return r >= 0.098 or r <= -0.098


def _turnover_proxy(avg_amount, price, volumes):
    if price <= 0:
        return 0.0
    shares_amount = avg_amount / price
    base = max(_mean(volumes[-60:]) if volumes else 1.0, 1.0)
    return shares_amount / base


def _refresh_financial_factors(C, rows, date):
    if getattr(C, "finance_disabled", False):
        C.finance_coverage = 0.0
        return
    fields = _finance_field_candidates()
    stocks = [r["stock"] for r in rows]
    if not stocks:
        C.finance_coverage = 0.0
        return
    start = _finance_start_date(date)
    updated = {}
    success_fields = 0
    error_count = 0
    for chunk in _chunks(stocks, C.finance_chunk_size):
        try:
            data = C.get_financial_data(fields, chunk, start, date)
            for field in fields:
                got_field = False
                for stock in chunk:
                    value = _extract_financial_value(data, stock, field)
                    if value is None:
                        continue
                    if stock not in updated:
                        updated[stock] = {}
                    updated[stock][field] = value
                    got_field = True
                if got_field:
                    success_fields += 1
            continue
        except Exception:
            error_count += 1
            pass

        for field in fields:
            try:
                data = C.get_financial_data([field], chunk, start, date)
            except Exception:
                error_count += 1
                continue
            got_field = False
            for stock in chunk:
                value = _extract_financial_value(data, stock, field)
                if value is None:
                    continue
                if stock not in updated:
                    updated[stock] = {}
                updated[stock][field] = value
                got_field = True
            if got_field:
                success_fields += 1

    for stock, data in updated.items():
        C.finance_cache[stock] = data
    covered = 0
    for stock in stocks:
        if stock in C.finance_cache and C.finance_cache[stock]:
            covered += 1
    C.finance_coverage = covered / float(len(stocks))
    if success_fields == 0:
        C.finance_error_count += error_count
    else:
        C.finance_error_count = 0
    if C.finance_error_count >= 60:
        C.finance_disabled = True
        print("%s V4_FINANCE disabled=1 reason=no_supported_fields_or_permission" % date)
    print("%s V4_FINANCE fields_ok=%d coverage=%.2f pool=%d" %
          (date, success_fields, C.finance_coverage, len(stocks)))


def _finance_field_candidates():
    return [
        "PERSHAREINDEX.s_fa_roe",
        "PERSHAREINDEX.roe",
        "PERSHAREINDEX.s_fa_roa",
        "PERSHAREINDEX.s_fa_grossprofitmargin",
        "PERSHAREINDEX.s_fa_netprofitmargin",
        "PERSHAREINDEX.s_fa_eps_basic",
        "PERSHAREINDEX.s_fa_bps",
        "PERSHAREINDEX.s_fa_ocfps",
        "PERSHAREINDEX.s_fa_yoy_or",
        "PERSHAREINDEX.s_fa_yoynetprofit",
        "PERSHAREINDEX.inc_revenue",
        "CAPITALSTRUCTURE.total_capital",
        "CAPITALSTRUCTURE.circulating_capital"
    ]


def _add_financial_features(C, rows):
    for row in rows:
        data = C.finance_cache.get(row["stock"], {})
        price = row["price"]
        roe = _first_value(data, ["PERSHAREINDEX.s_fa_roe", "PERSHAREINDEX.roe"])
        roa = _first_value(data, ["PERSHAREINDEX.s_fa_roa"])
        gross = _first_value(data, ["PERSHAREINDEX.s_fa_grossprofitmargin"])
        net_margin = _first_value(data, ["PERSHAREINDEX.s_fa_netprofitmargin"])
        eps = _first_value(data, ["PERSHAREINDEX.s_fa_eps_basic"])
        bps = _first_value(data, ["PERSHAREINDEX.s_fa_bps"])
        ocfps = _first_value(data, ["PERSHAREINDEX.s_fa_ocfps"])
        yoy_or = _first_value(data, ["PERSHAREINDEX.s_fa_yoy_or", "PERSHAREINDEX.inc_revenue"])
        yoy_np = _first_value(data, ["PERSHAREINDEX.s_fa_yoynetprofit"])

        value_parts = []
        if eps is not None and price > 0:
            value_parts.append(_clip(eps / price, -0.5, 0.5))
        if bps is not None and price > 0:
            value_parts.append(_clip(bps / price, -2.0, 4.0))
        if ocfps is not None and price > 0:
            value_parts.append(_clip(ocfps / price, -1.0, 1.0))

        quality_parts = []
        for x in [roe, roa, gross, net_margin]:
            if x is not None:
                quality_parts.append(_clip(_percent_to_decimal(x), -1.0, 1.0))

        growth_parts = []
        for x in [yoy_or, yoy_np]:
            if x is not None:
                growth_parts.append(_clip(_percent_to_decimal(x), -1.0, 1.5))

        row["value"] = _mean(value_parts) if value_parts else None
        row["quality"] = _mean(quality_parts) if quality_parts else None
        row["growth"] = _mean(growth_parts) if growth_parts else None


def _standardize_and_score(C, rows):
    for field in [
        "mom20", "mom60", "mom120", "rev5", "low_vol20", "low_vol60",
        "liquidity", "breakout", "trend_quality", "value", "quality",
        "growth", "turnover", "flow"
    ]:
        _standardize(rows, field)

    finance_weight = 0.24 if C.finance_coverage >= 0.20 else 0.08
    price_weight = 1.0 - finance_weight
    for row in rows:
        price_score = (
            0.16 * row["mom20_z"] +
            0.24 * row["mom60_z"] +
            0.18 * row["mom120_z"] +
            0.10 * row["rev5_z"] +
            0.10 * row["low_vol20_z"] +
            0.08 * row["low_vol60_z"] +
            0.07 * row["liquidity_z"] +
            0.04 * row["breakout_z"] +
            0.03 * row["trend_quality_z"]
        )
        finance_score = (
            0.34 * row["value_z"] +
            0.36 * row["quality_z"] +
            0.22 * row["growth_z"] +
            0.04 * row["turnover_z"] +
            0.04 * row["flow_z"]
        )
        row["base_score"] = price_weight * price_score + finance_weight * finance_score
        row["score"] = row["base_score"]


def _standardize(rows, field):
    values = []
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        try:
            v = float(value)
        except Exception:
            continue
        if math.isfinite(v):
            values.append(v)
    mu = _mean(values)
    sd = _std(values)
    for row in rows:
        value = row.get(field)
        z = 0.0
        if value is not None and sd > 1e-12:
            try:
                z = (float(value) - mu) / sd
            except Exception:
                z = 0.0
        row[field + "_z"] = _clip(z, -3.0, 3.0)


def _update_ml_model(C, rows):
    current = {}
    for row in rows:
        feature = {}
        for name in C.ml_features:
            feature[name] = row.get(name, 0.0)
        current[row["stock"]] = {"price": row["price"], "feature": feature}

    ready = []
    kept = []
    for sample in C.ml_pending:
        if C.barpos - sample["barpos"] >= C.ml_horizon:
            ready.append(sample)
        else:
            kept.append(sample)
    C.ml_pending = kept

    observations = []
    for sample in ready:
        for stock, old in sample["data"].items():
            if stock not in current:
                continue
            old_price = old["price"]
            new_price = current[stock]["price"]
            if old_price <= 0 or new_price <= 0:
                continue
            ret = new_price / old_price - 1.0
            observations.append((old["feature"], ret))

    if len(observations) >= C.ml_min_samples:
        weights = {}
        for name in C.ml_features:
            xs = [obs[0].get(name, 0.0) for obs in observations]
            ys = [obs[1] for obs in observations]
            weights[name] = _corr(xs, ys)
        norm = sum(abs(v) for v in weights.values())
        if norm > 1e-12:
            for name in weights:
                weights[name] = weights[name] / norm
            if not C.ml_weights:
                C.ml_weights = weights
            else:
                for name in weights:
                    C.ml_weights[name] = 0.70 * C.ml_weights.get(name, 0.0) + 0.30 * weights[name]
            C.ml_sample_count += len(observations)

    sample_data = {}
    for row in rows[:C.finance_pool_limit]:
        feature = {}
        for name in C.ml_features:
            feature[name] = row.get(name, 0.0)
        sample_data[row["stock"]] = {"price": row["price"], "feature": feature}
    C.ml_pending.append({"barpos": C.barpos, "data": sample_data})


def _apply_ml_score(C, rows):
    if not C.ml_weights:
        for row in rows:
            row["ml_score"] = 0.0
        return
    for row in rows:
        ml = 0.0
        for name, weight in C.ml_weights.items():
            ml += weight * row.get(name, 0.0)
        row["ml_score"] = _clip(ml, -3.0, 3.0)
        row["score"] = (1.0 - C.ml_blend) * row["base_score"] + C.ml_blend * row["ml_score"]


def _select_with_industry_cap(C, ranked, target_num):
    selected = []
    counts = {}
    max_per_industry = max(2, int(math.ceil(target_num * 0.18)))
    for row in ranked:
        industry = row["industry"]
        if counts.get(industry, 0) >= max_per_industry:
            continue
        selected.append(row)
        counts[industry] = counts.get(industry, 0) + 1
        if len(selected) >= target_num:
            return selected
    for row in ranked:
        if row in selected:
            continue
        selected.append(row)
        if len(selected) >= target_num:
            break
    return selected


def _allocate_inverse_vol_weights(C, selected, target_position):
    weights = {}
    if not selected:
        return weights
    raw = {}
    for row in selected:
        vol = max(row.get("vol20", 0.0), 0.006)
        raw[row["stock"]] = 1.0 / vol
    raw_sum = sum(raw.values())
    industry_total = {}
    for row in selected:
        stock = row["stock"]
        industry = row["industry"]
        desired = target_position * raw[stock] / raw_sum if raw_sum > 0 else target_position / len(selected)
        desired = min(desired, C.max_single_weight)
        room = C.max_industry_weight - industry_total.get(industry, 0.0)
        weight = max(0.0, min(desired, room))
        weights[stock] = weight
        industry_total[industry] = industry_total.get(industry, 0.0) + weight

    for _ in range(3):
        current = sum(weights.values())
        residual = target_position - current
        if residual <= 0.005:
            break
        candidates = []
        for row in selected:
            stock = row["stock"]
            industry = row["industry"]
            single_room = C.max_single_weight - weights.get(stock, 0.0)
            industry_room = C.max_industry_weight - industry_total.get(industry, 0.0)
            room = min(single_room, industry_room)
            if room > 0.001:
                candidates.append((row, room))
        if not candidates:
            break
        add_each = residual / len(candidates)
        for row, room in candidates:
            stock = row["stock"]
            industry = row["industry"]
            add = min(room, add_each)
            weights[stock] = weights.get(stock, 0.0) + add
            industry_total[industry] = industry_total.get(industry, 0.0) + add
    return weights


def _rebalance(C, date, weights, close_map):
    holding = _get_holdings(C.accountid, "stock")
    asset = _get_total_asset(C.accountid, "stock", C.initial_cash)
    target_shares = {}
    for stock, weight in weights.items():
        price = _last_price(close_map, stock)
        if price <= 0:
            continue
        shares = int((asset * weight / price) / 100) * 100
        target_shares[stock] = max(shares, 0)

    all_stocks = set(holding.keys()) | set(target_shares.keys())
    for stock in all_stocks:
        current = int(holding.get(stock, 0))
        target = int(target_shares.get(stock, 0))
        delta = target - current
        if abs(delta) < C.trade_threshold_shares:
            continue
        price = _last_price(close_map, stock)
        if price <= 0:
            continue
        prices = _series(close_map.get(stock, []))
        if delta > 0 and _is_limit_up(prices):
            continue
        if delta < 0 and _is_limit_down(prices):
            continue
        try:
            order_shares(stock, delta, "FIX", price, C, C.accountid)
            score = _find_score_for_log(stock, weights)
            print("%s V4_ORDER %s delta=%d target=%d price=%.3f weight=%.4f" %
                  (date, stock, delta, target, price, weights.get(stock, 0.0)))
        except Exception as err:
            print("%s V4_ORDER_WARN %s delta=%d err=%s" % (date, stock, delta, err))


def _market_state(C, close_map):
    prices = _series(close_map.get(C.benchmark, []))
    if len(prices) < 80:
        return "normal", C.target_position_normal, 0.0
    mom20 = _ret(prices, 20)
    mom60 = _ret(prices, 60)
    ma20 = _mean(prices[-20:])
    ma60 = _mean(prices[-60:])
    vol60 = _return_std(prices[-61:]) * math.sqrt(252.0)
    price = prices[-1]
    if mom60 > 0.08 and price > ma20 and price > ma60:
        return "bull", C.target_position_bull, mom60
    if mom60 < -0.10 or price < 0.94 * ma60:
        return "bear", C.target_position_bear, mom60
    if mom20 < -0.04 or vol60 > 0.30 or price < ma20:
        return "weak", C.target_position_weak, mom60
    return "normal", C.target_position_normal, mom60


def _update_stage_stats(C, date, market_state, target_position, valid_count, selected):
    stage = _stage_name(date)
    stat = C.stage_stats.get(stage, {
        "rebalance": 0,
        "valid_sum": 0,
        "selected_sum": 0,
        "target_sum": 0.0,
        "finance_sum": 0.0
    })
    stat["rebalance"] += 1
    stat["valid_sum"] += valid_count
    stat["selected_sum"] += len(selected)
    stat["target_sum"] += target_position
    stat["finance_sum"] += C.finance_coverage
    C.stage_stats[stage] = stat
    if stat["rebalance"] % 20 == 1:
        avg_valid = stat["valid_sum"] / float(stat["rebalance"])
        avg_target = stat["target_sum"] / float(stat["rebalance"])
        avg_fin = stat["finance_sum"] / float(stat["rebalance"])
        print("%s V4_STAGE stage=%s n=%d state=%s avg_valid=%.1f avg_target=%.2f avg_finance=%.2f" %
              (date, stage, stat["rebalance"], market_state, avg_valid, avg_target, avg_fin))


def _stage_name(date):
    try:
        year = int(str(date)[:4])
    except Exception:
        return "other"
    if year == 2018:
        return "2018_bear"
    if 2019 <= year <= 2021:
        return "2019_2021_bull"
    if year == 2022:
        return "2022_drawdown"
    if 2023 <= year <= 2026:
        return "2023_2026_choppy"
    return "other"


def _finance_start_date(date):
    s = str(date)
    if len(s) < 8:
        return s
    try:
        y = int(s[:4]) - 3
        return "%04d%s" % (y, s[4:8])
    except Exception:
        return s


def _extract_financial_value(data, stock, field):
    probes = []
    try:
        probes.append(data[stock][field])
    except Exception:
        pass
    try:
        probes.append(data[stock][field].values)
    except Exception:
        pass
    try:
        probes.append(data.loc[stock, field])
    except Exception:
        pass
    try:
        probes.append(data[field][stock])
    except Exception:
        pass
    try:
        probes.append(data[stock].loc[:, field])
    except Exception:
        pass
    for item in probes:
        value = _latest_number(item)
        if value is not None:
            return value
    return None


def _latest_number(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    try:
        vals = list(x)
    except Exception:
        try:
            v = float(x)
            return v if math.isfinite(v) else None
        except Exception:
            return None
    for item in reversed(vals):
        v = _latest_number(item)
        if v is not None:
            return v
    return None


def _first_value(data, fields):
    for field in fields:
        if field in data:
            value = _latest_number(data[field])
            if value is not None:
                return value
    return None


def _percent_to_decimal(x):
    if x is None:
        return None
    v = float(x)
    if abs(v) > 2.0:
        return v / 100.0
    return v


def _chunks(xs, size):
    for i in range(0, len(xs), size):
        yield xs[i:i + size]


def _is_a_share(stock):
    return isinstance(stock, str) and (stock.endswith(".SH") or stock.endswith(".SZ"))


def _prefix_group(stock):
    code = str(stock).split(".")[0]
    return "prefix_" + code[:2]


def _breakout_score(high_map, low_map, prices, stock):
    highs = _series(high_map.get(stock, []))
    lows = _series(low_map.get(stock, []))
    if len(highs) < 20 or len(lows) < 20:
        window = prices[-20:]
        hi = max(window)
        lo = min(window)
    else:
        hi = max(highs[-20:])
        lo = min(lows[-20:])
    if hi <= lo:
        return 0.0
    return (prices[-1] - lo) / (hi - lo)


def _trend_quality(prices):
    if len(prices) < 20:
        return 0.0
    up = 0
    total = 0
    for i in range(1, len(prices)):
        if prices[i - 1] <= 0:
            continue
        total += 1
        if prices[i] > prices[i - 1]:
            up += 1
    return up / float(total) if total > 0 else 0.0


def _ret(prices, n):
    if len(prices) <= n or prices[-1 - n] <= 0:
        return 0.0
    return prices[-1] / prices[-1 - n] - 1.0


def _corr(xs, ys):
    if len(xs) != len(ys) or len(xs) < 3:
        return 0.0
    mx = _mean(xs)
    my = _mean(ys)
    vx = sum((x - mx) * (x - mx) for x in xs)
    vy = sum((y - my) * (y - my) for y in ys)
    if vx <= 1e-12 or vy <= 1e-12:
        return 0.0
    cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs)))
    return cov / math.sqrt(vx * vy)


def _is_limit_up(prices):
    if len(prices) < 2 or prices[-2] <= 0:
        return False
    return prices[-1] / prices[-2] - 1.0 >= 0.098


def _is_limit_down(prices):
    if len(prices) < 2 or prices[-2] <= 0:
        return False
    return prices[-1] / prices[-2] - 1.0 <= -0.098


def _get_holdings(accountid, datatype):
    holding = {}
    try:
        result = get_trade_detail_data(accountid, datatype, "POSITION")
        for obj in result:
            code = obj.m_strInstrumentID + "." + obj.m_strExchangeID
            holding[code] = int(obj.m_nVolume)
    except Exception as err:
        print("V4_WARN holdings_error=%s" % err)
    return holding


def _get_total_asset(accountid, datatype, fallback):
    try:
        account = get_trade_detail_data(accountid, datatype, "ACCOUNT")
        if account:
            for name in ["m_dBalance", "m_dAsset", "m_dAvailable"]:
                if hasattr(account[0], name):
                    value = float(getattr(account[0], name))
                    if value > 0:
                        return value
    except Exception:
        pass
    return fallback


def _date_str(C):
    try:
        return timetag_to_datetime(C.get_bar_timetag(C.barpos), "%Y%m%d")
    except Exception:
        return str(C.barpos)


def _series(xs):
    out = []
    for x in xs:
        try:
            v = float(x)
        except Exception:
            continue
        if math.isfinite(v):
            out.append(v)
    return out


def _last_price(close_map, stock):
    prices = _series(close_map.get(stock, []))
    return prices[-1] if prices else 0.0


def _mean(xs):
    return sum(xs) / float(len(xs)) if xs else 0.0


def _std(xs):
    if len(xs) < 2:
        return 0.0
    mu = _mean(xs)
    var = sum((x - mu) * (x - mu) for x in xs) / float(len(xs))
    return math.sqrt(max(var, 0.0))


def _return_std(prices):
    rets = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            rets.append(prices[i] / prices[i - 1] - 1.0)
    return _std(rets)


def _clip(x, lo, hi):
    try:
        v = float(x)
    except Exception:
        return 0.0
    if not math.isfinite(v):
        return 0.0
    return max(lo, min(hi, v))


def _find_score_for_log(stock, weights):
    return weights.get(stock, 0.0)


def _paint(C, valid_count, target_position, market_mom60, selected_count, finance_coverage, ml_sample_count):
    C.paint("valid_count", valid_count, -1, 0)
    C.paint("target_pos", target_position, -1, 0)
    C.paint("market_mom60", market_mom60, -1, 0)
    C.paint("selected_count", selected_count, -1, 0)
    C.paint("finance_cov", finance_coverage, -1, 0)
    C.paint("ml_samples", ml_sample_count, -1, 0)
