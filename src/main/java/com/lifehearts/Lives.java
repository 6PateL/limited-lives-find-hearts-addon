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

    /**
     * Нагорода серця: +1 життя з посвяченням (екранний ефект, урочисті звуки, частинки). Екранний ефект показується
     * завжди; якщо життя вже повні або Limited Lives немає — замість життя лікування / поглинання.
     */
    public static void reward(net.minecraft.server.level.ServerPlayer p, String source) {
        int lives = giveLife(p);
        Net.sendLifeFx(p, lives);
        p.playNotifySound(net.minecraft.sounds.SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, net.minecraft.sounds.SoundSource.PLAYERS, 1.0F, 1.0F);
        p.playNotifySound(net.minecraft.sounds.SoundEvents.BEACON_ACTIVATE, net.minecraft.sounds.SoundSource.PLAYERS, 1.0F, 1.3F);
        p.playNotifySound(net.minecraft.sounds.SoundEvents.TOTEM_USE, net.minecraft.sounds.SoundSource.PLAYERS, 0.4F, 1.4F);
        ((net.minecraft.server.level.ServerLevel) p.level()).sendParticles(net.minecraft.core.particles.ParticleTypes.TOTEM_OF_UNDYING,
                p.getX(), p.getY() + 1.0D, p.getZ(), 60, 0.5D, 1.0D, 0.5D, 0.3D);
        if (lives == -2) {
            p.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.REGENERATION, 200, 1));
            p.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.ABSORPTION, 1200, 1));
            p.displayClientMessage(net.minecraft.network.chat.Component.translatable("msg.lifehearts.full")
                    .withStyle(net.minecraft.ChatFormatting.GOLD), true);
            LifeHearts.LOG.info("[LifeHearts] {} took a heart ({}), lives already full: healed instead", p.getName().getString(), source);
            return;
        }
        if (lives == -1) {
            p.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.ABSORPTION, 2400, 3));
            p.displayClientMessage(net.minecraft.network.chat.Component.translatable("msg.lifehearts.nomod")
                    .withStyle(net.minecraft.ChatFormatting.GOLD), true);
            LifeHearts.LOG.info("[LifeHearts] {} took a heart ({}), Limited Lives not available: absorption instead", p.getName().getString(), source);
            return;
        }
        p.sendSystemMessage(net.minecraft.network.chat.Component.translatable("msg.lifehearts.gained", lives)
                .withStyle(net.minecraft.ChatFormatting.RED, net.minecraft.ChatFormatting.BOLD));
        LifeHearts.LOG.info("[LifeHearts] {} gained a life ({}): now {} lives", p.getName().getString(), source, lives);
    }
}
