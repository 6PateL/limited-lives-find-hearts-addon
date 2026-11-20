package com.lifehearts;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RenderGuiEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Ефект «посвячення»: екран заливає тепле червоно-золоте сяйво від країв, у центрі виростає й пульсує серце з написом
 * «+1 життя», потім усе плавно згасає.
 */
@Mod.EventBusSubscriber(modid = LifeHearts.MOD_ID, value = Dist.CLIENT)
public final class LifeOverlay {
    private static final long IN = 500L, HOLD = 1800L, OUT = 1400L;
    private static long started = -1L;
    private static int lives;

    private LifeOverlay() {}

    static void start(int l) {
        started = System.currentTimeMillis();
        lives = l;
    }

    // піксельне серце 9x8
    private static final String[] HEART = {
            ".XX...XX.",
            "XXXX.XXXX",
            "XXXXXXXXX",
            "XXXXXXXXX",
            ".XXXXXXX.",
            "..XXXXX..",
            "...XXX...",
            "....X...."};

    @SubscribeEvent
    public static void onRender(RenderGuiEvent.Post event) {
        if (started < 0L) {
            return;
        }
        long t = System.currentTimeMillis() - started;
        if (t > IN + HOLD + OUT) {
            started = -1L;
            return;
        }
        float a = t < IN ? t / (float) IN : t < IN + HOLD ? 1.0F : 1.0F - (t - IN - HOLD) / (float) OUT;
        a = a * a * (3.0F - 2.0F * a);
        GuiGraphics g = event.getGuiGraphics();
        int w = event.getWindow().getGuiScaledWidth(), h = event.getWindow().getGuiScaledHeight();
        // сяйво від країв
        int band = Math.min(w, h) / 3;
        int edge = argb((int) (150 * a), 0xFF, 0x50, 0x40), gold = argb((int) (60 * a), 0xFF, 0xC8, 0x40), none = argb(0, 0xFF, 0x50, 0x40);
        g.fillGradient(0, 0, w, band, edge, none);
        g.fillGradient(0, h - band, w, h, none, edge);
        g.fill(0, 0, w, h, gold);
        // серце, що виростає з пульсом
        float grow = Math.min(1.0F, t / 450.0F);
        float pulse = 1.0F + 0.08F * (float) Math.sin(t / 1000.0D * Math.PI * 2.0D * 1.3D);
        int px = Math.max(2, (int) (Math.min(w, h) / 50.0F * grow * pulse));
        int ox = w / 2 - 9 * px / 2, oy = h / 2 - 8 * px / 2 - h / 10;
        for (int y = 0; y < HEART.length; y++) {
            for (int x = 0; x < HEART[y].length(); x++) {
                if (HEART[y].charAt(x) != 'X') {
                    continue;
                }
                boolean shine = (x == 1 || x == 2) && y <= 2;
                g.fill(ox + x * px, oy + y * px, ox + (x + 1) * px, oy + (y + 1) * px,
                        shine ? argb((int) (255 * a), 0xFF, 0xB0, 0xB0) : argb((int) (255 * a), 0xE0, 0x18, 0x28));
            }
        }
        Minecraft mc = Minecraft.getInstance();
        Component text = Component.translatable("overlay.lifehearts.plus");
        g.pose().pushPose();
        g.pose().translate(w / 2.0F, oy + 8 * px + 10, 0.0F);
        g.pose().scale(2.0F, 2.0F, 1.0F);
        g.drawCenteredString(mc.font, text, 0, 0, (Math.max(8, (int) (255 * a)) << 24) | 0xFFD84A);
        g.pose().popPose();
        if (lives > 0) {
            g.drawCenteredString(mc.font, Component.translatable("overlay.lifehearts.lives", lives), w / 2, oy + 8 * px + 34,
                    (Math.max(8, (int) (255 * a)) << 24) | 0xFFFFFF);
        }
    }

    private static int argb(int a, int r, int g, int b) {
        return (Math.max(0, Math.min(255, a)) << 24) | (r << 16) | (g << 8) | b;
    }
}
