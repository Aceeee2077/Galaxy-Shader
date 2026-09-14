import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.List;
import net.irisshaders.iris.shaderpack.parsing.ConstDirectiveParser;
import net.irisshaders.iris.shaderpack.parsing.DispatchingDirectiveHolder;
import org.joml.Vector4f;
import net.irisshaders.iris.shaderpack.preprocessor.JcppProcessor;
import net.irisshaders.iris.shaderpack.properties.PackRenderTargetDirectives;

/** Executes the real Iris CPU parser from the supplied release JAR. */
public class IrisDirectiveCheck {
    public static void main(String[] args) throws Exception {
        Map<String, Vector4f> received = new LinkedHashMap<>();
        var holder = new DispatchingDirectiveHolder();
        var constructor = PackRenderTargetDirectives.class.getDeclaredConstructor(Set.class);
        constructor.setAccessible(true);
        var targets = constructor.newInstance(Set.of(0,1,2,3,4,5,6,7));
        targets.acceptDirectives(holder);
        for (int i : new int[] {0, 1, 2, 3, 7}) {
            String name = "colortex" + i + "ClearColor";
            holder.acceptConstVec4Directive(name, value -> received.put(name, value));
        }
        String source = JcppProcessor.glslPreprocessSource(Files.readString(Path.of(args[0])), List.of());
        for (var directive : ConstDirectiveParser.findDirectives(source)) {
            holder.processDirective(directive);
        }
        if (received.size() != 5) throw new AssertionError("Missing callbacks: " + received);
        for (int i : new int[] {0, 2, 3, 7}) {
            if (!received.get("colortex" + i + "ClearColor").equals(new Vector4f(0, 0, 0, 0)))
                throw new AssertionError("Incorrect clear color " + i);
        }
        if (!received.get("colortex1ClearColor").equals(new Vector4f(0.5f, 0.5f, 1, 1)))
            throw new AssertionError("Incorrect normal clear color");
        String[] expected = {"RGBA16F", "RGBA16F", "RGBA16F", "RGBA8", "RGBA16F", "R11F_G11F_B10F", "R11F_G11F_B10F", "RGBA16F"};
        for (int i=0; i<expected.length; i++) {
            String actual = targets.getRenderTargetSettings().get(i).getInternalFormat().name();
            if (!expected[i].equals(actual)) throw new AssertionError("Wrong format at " + i + ": " + actual);
        }
        if (targets.getRenderTargetSettings().get(7).shouldClear())
            throw new AssertionError("Temporal history target must persist between frames");
        System.out.println("PASS: actual Iris preprocessor and render-target parser accepted 8 exact formats, 5 exact clear colors, and persistent colortex7.");
    }
}
