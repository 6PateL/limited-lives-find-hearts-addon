package com.lifehearts;

import net.minecraft.server.level.ServerPlayer;

/** Міст до Limited Lives (через рефлексію: мод необов'язковий). Життя = максимум − кількість смертей. */
public final class Lives {
    private Lives() {}

    private static Object api() throws Exception {
        return Class.forName("me.ichun.mods.limitedlives.api.LimitedLivesApi").getMethod("getApiImpl").invoke(null);
    }

    private static Class<?> iface() throws Exception {
        return Class.forName("me.ichun.mods.limitedlives.api.IApi");
    }

    /** Кількість смертей гравця або -2147483648, якщо Limited Lives немає. */
    static int deaths(ServerPlayer p) {
        try {
            return (Integer) iface().getMethod("getPlayerDeaths", ServerPlayer.class).invoke(api(), p);
        } catch (Throwable t) {
            return Integer.MIN_VALUE;
        }
    }

    static int maxLives() {
        try {
            Class<?> ll = Class.forName("me.ichun.mods.limitedlives.common.LimitedLives");
            Object cfg = ll.getField("config").get(null);
            return cfg.getClass().getField("maxLives").getInt(cfg);
        } catch (Throwable t) {
            return -1;
        }
    }

    /** Повертає одне життя (на одну смерть менше). @return нова кількість життів або -1, якщо не вийшло */
    static int giveLife(ServerPlayer p) {
        int d = deaths(p);
        if (d == Integer.MIN_VALUE) {
            return -1;
        }
        if (d <= -HeartConfig.EXTRA_LIVES.get()) {
            return -2; // уже повні життя
        }
        try {
            iface().getMethod("setPlayerDeaths", ServerPlayer.class, int.class, boolean.class).invoke(api(), p, d - 1, true);
        } catch (Throwable t) {
            LifeHearts.LOG.warn("[LifeHearts] could not change lives of {}: {}", p.getName().getString(), t.toString());
            return -1;
        }
        int max = maxLives();
        return max < 0 ? 0 : max - (d - 1);
    }
}
