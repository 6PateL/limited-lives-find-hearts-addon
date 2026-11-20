package com.lifehearts;

import net.minecraftforge.common.ForgeConfigSpec;

public final class HeartConfig {
    public static final ForgeConfigSpec SPEC;
    public static final ForgeConfigSpec.BooleanValue ENABLED;
    public static final ForgeConfigSpec.IntValue CHECK_SECONDS;
    public static final ForgeConfigSpec.DoubleValue CHANCE;
    public static final ForgeConfigSpec.IntValue MIN_DIST;
    public static final ForgeConfigSpec.IntValue MAX_DIST;
    public static final ForgeConfigSpec.IntValue MAX_NEARBY;
    public static final ForgeConfigSpec.IntValue LIFETIME_MINUTES;
    public static final ForgeConfigSpec.IntValue HITS;
    public static final ForgeConfigSpec.IntValue EXTRA_LIVES;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.push("spawning");
        ENABLED = b.comment("Hearts appear in the world on their own.").define("enabled", true);
        CHECK_SECONDS = b.comment("How often (seconds) each player gets a chance for a heart nearby.").defineInRange("checkSeconds", 120, 10, 36000);
        CHANCE = b.comment("Chance per check. 0.1 every 120 s = about one heart per 20 minutes of play per player.").defineInRange("chance", 0.1D, 0.0D, 1.0D);
        MIN_DIST = b.comment("Closest distance from the player.").defineInRange("minDistance", 24, 4, 200);
        MAX_DIST = b.comment("Farthest distance from the player.").defineInRange("maxDistance", 64, 8, 256);
        MAX_NEARBY = b.comment("No new heart while this many already exist within 160 blocks.").defineInRange("maxNearby", 2, 1, 50);
        LIFETIME_MINUTES = b.comment("A heart nobody broke fades away after this many minutes (0 = never).").defineInRange("lifetimeMinutes", 60, 0, 100000);
        b.pop();
        b.push("heart");
        HITS = b.comment("Hits needed to break a heart.").defineInRange("hits", 3, 1, 50);
        EXTRA_LIVES = b.comment("How many lives a player may have above the Limited Lives maximum thanks to hearts (0 = never above the maximum).")
                .defineInRange("extraLivesAboveMax", 0, 0, 100);
        b.pop();
        SPEC = b.build();
    }

    private HeartConfig() {}
}
