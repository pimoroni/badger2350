#include <algorithm>

#include "picovector.hpp"
#include "brush.hpp"
#include "image.hpp"
#include "shape.hpp"
#include "font.hpp"
#include "types.hpp"
#include "mat3.hpp"
#include "blend.hpp"

using std::sort, std::min, std::max;

// memory pool for rasterisation, png decoding, and other memory intensive
// tasks (sized to fit PNGDEC state) - on pico it *must* be 32bit aligned (i
// found out the hard way.)
char __attribute__((aligned(4))) PicoVector_working_buffer[working_buffer_size];

#define TILE_WIDTH 64
#define TILE_HEIGHT 64
#define MAX_NODES_PER_SCANLINE 64

#define TILE_BUFFER_SIZE (TILE_WIDTH * (TILE_HEIGHT + 1) * sizeof(uint8_t)) // ~4kB tile buffer
#define NODE_BUFFER_ROW_SIZE (MAX_NODES_PER_SCANLINE * sizeof(int16_t))
#define NODE_BUFFER_SIZE (TILE_HEIGHT * 4 * NODE_BUFFER_ROW_SIZE) // 32kB node buffer
#define NODE_COUNT_BUFFER_SIZE (TILE_HEIGHT * 4 * sizeof(uint8_t)) // 256 byte node count buffer

// buffer that each tile is rendered into before callback
uint8_t *tile_buffer = (uint8_t *)&PicoVector_working_buffer[0];
int16_t *node_buffer = (int16_t *)&PicoVector_working_buffer[TILE_BUFFER_SIZE];
uint8_t *node_count_buffer = (uint8_t *)&PicoVector_working_buffer[TILE_BUFFER_SIZE + NODE_BUFFER_SIZE];

static inline void insertion_sort_i16(int16_t* a, int n) {
  for (int i = 1; i < n; ++i) {
    int16_t key = a[i];
    int j = i - 1;
    while (j >= 0 && a[j] > key) {
      a[j + 1] = a[j];
      --j;
    }
    a[j + 1] = key;
  }
}

namespace picovector {

  int sign(int v) {return (v > 0) - (v < 0);}

  void add_line_segment_to_nodes(vec2_t start, vec2_t end, rect_t *tb) {
    if(end.y < start.y) {
      vec2_t tmp = start; start = end; end = tmp;
    }

    if (end.y < 0.0f || start.y > tb->h || end.y == start.y) return;

    float x = start.x;
    float dx = (end.x - start.x) / (end.y - start.y);

    if(start.y < 0.0f) {
      x += fabs(start.y) * dx;
      start.y = 0.0f;
    }

    if(end.y > tb->h) {
      end.y = tb->h;
    }

    int minx = 0;
    int maxx = ceilf(tb->w);

    int sy = int(start.y);
    int ey = int(end.y);

    for(int iy = sy; iy < ey; iy++) {
      int ix = max(min(int(x), maxx), minx);

      node_buffer[(iy * MAX_NODES_PER_SCANLINE) + node_count_buffer[iy]] = ix;
      node_count_buffer[iy]++;

      x += dx;
    }
  }

  void build_nodes(path_t *path, rect_t *tb, mat3_t *transform, uint aa) {
    vec2_t offset = tb->tl();
    // start with the last point to close the loop, transform it, scale for antialiasing, and offset to tile origin
    vec2_t last = path->points[path->points.size() - 1];
    if(transform) last = last.transform(transform);
    last *= (1 << aa);
    last -= offset;

    for(auto next : path->points) {
      if(transform) next = next.transform(transform);
      next *= (1 << aa);
      next -= offset;

      //printf("   - add line segment %d, %d -> %d, %d\n", int(last.x), int(last.y), int(next.x), int(next.y));
      add_line_segment_to_nodes(last, next, tb);
      last = next;
    }
  }

  int compare_nodes(const void* a, const void* b) {
    return *((int16_t*)a) - *((int16_t*)b);
  }

  uint8_t alpha_map_none[2] = {0, 255};
  uint8_t alpha_map_x4[5] = {0, 63, 127, 190, 255};
  uint8_t alpha_map_x16[17] = {0, 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240, 255};

  rect_t render_nodes(rect_t *tb, uint aa) {
    int minx = tb->w;
    int miny = tb->h;
    int maxx = 0;
    int maxy = 0;

    for(int y = 0; y < int(tb->h); y++) {
      if(node_count_buffer[y] == 0) {
        continue; // no nodes on this raster line
      }

      miny = min(miny, y);
      maxy = max(maxy, y);

      // sort scanline nodes
      int16_t *nodes = &node_buffer[(y * MAX_NODES_PER_SCANLINE)];
      insertion_sort_i16(nodes, node_count_buffer[y]);

      uint8_t *row_data = &tile_buffer[(y >> aa) * TILE_WIDTH];

      for(uint32_t i = 0; i < node_count_buffer[y]; i += 2) {
        int sx = *nodes++;
        int ex = *nodes++;

        if(sx == ex) { // empty span, nothing to do
          continue;
        }

        minx = min(minx, sx);
        maxx = max(maxx, ex);

        do {
          row_data[sx >> aa]++;
        } while(++sx < ex);
      }

      // for(int i = 0; i < TILE_WIDTH; i++) {
      //   row_data[i] = 1;
      // }


    }

    if(minx > maxx || miny > maxy) {
      return rect_t(0, 0, 0, 0);
    }

    int out_minx = (minx >> aa);
    int out_maxx = ((maxx + (1 << aa) - 1) >> aa);
    int out_miny = (miny >> aa);
    int out_maxy = ((maxy + (1 << aa) - 1) >> aa);

    return rect_t(out_minx, out_miny,
              (out_maxx - out_minx),
              (out_maxy - out_miny) + 1);
  }

  void render(shape_t *shape, image_t *target, mat3_t *transform, brush_t *brush) {

    if(shape->paths.empty()) return;

    // antialias level of target image
    uint aa = (uint)target->antialias();

    uint8_t *p_alpha_map = alpha_map_none;
    if(aa == 1) p_alpha_map = alpha_map_x4;
    if(aa == 2) p_alpha_map = alpha_map_x16;

    //mask_span_func_t sf = target->_mask_span_func;
    //printf("render shape\n");

    // determine bounds of shape to be rendered
    rect_t sb = shape->bounds().round();

    rect_t clip = target->clip();

    masked_span_func_t fn = target->_masked_span_func;

    //printf("- shape bounds %d, %d (%d x %d)\n", sbx, sby, sbw, sbh);
    //printf("- clip bounds %d, %d (%d x %d)\n", int(clip.x), int(clip.y), int(clip.w), int(clip.h));

    // iterate over tiles
    //printf("> processing tiles\n");
    for(int y = sb.y; y < sb.y + sb.h; y += TILE_HEIGHT) {
      for(int x = sb.x; x < sb.x + sb.w; x += TILE_WIDTH) {
        //printf(" > tile %d x %d\n", x, y);
        rect_t tb = rect_t(x, y, TILE_WIDTH, TILE_HEIGHT);

        //printf("  - tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));

        tb = clip.intersection(tb).intersection(sb).round();
        if(tb.empty()) { continue; } // if tile empty, skip it

        //printf("  - clipped tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));
        // screen coordinates for clipped tile
        int sx = tb.x;
        int sy = tb.y;
        int sw = tb.w;
        int sh = tb.h;

        tb.x *= (1 << aa);
        tb.y *= (1 << aa);
        tb.w *= (1 << aa);
        tb.h *= (1 << aa);

        //printf("  - clipped and scaled tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));

        // clear existing tile data and nodes
        memset(node_count_buffer, 0, NODE_COUNT_BUFFER_SIZE);
        for (int row = 0; row <= sh; ++row) {
          memset(&tile_buffer[row * TILE_WIDTH], 0, sw);
        }

        //memset(tile_buffer, 0, TILE_WIDTH * TILE_HEIGHT);

        // build the nodes for each path
        for(auto &path : shape->paths) {
          build_nodes(&path, &tb, transform, aa);
        }

        rect_t rb = render_nodes(&tb, aa).round();

        if(tb.empty()) { continue; }

        int rbx = rb.x;
        int rby = rb.y;
        int rbw = rb.w;
        int rbh = rb.h;

        for(int ty = rby; ty < rby + rbh; ty++) {
          uint8_t* p;

          // scale tile buffer values to alpha values
          p = &tile_buffer[ty * TILE_WIDTH + rbx];
          int c = rbw;
          while(c--) {
            *p = p_alpha_map[*p];
            p++;
          }

          // render tile span
          p = &tile_buffer[ty * TILE_WIDTH + rbx];

          fn(target, brush, sx + rbx, sy + ty, rbw, p);
          //sf(target, brush, sx + rbx, sy + ty, rbw, (uint8_t*)p);
        }
      }
    }
  }






















  void build_glyph_nodes(glyph_path_t *path, rect_t *tb, mat3_t *transform, uint aa) {
    vec2_t offset = tb->tl();
    // start with the last point to close the loop, transform it, scale for antialiasing, and offset to tile origin
    glyph_path_point_t *p = &path->points[path->point_count - 1];
    vec2_t last = vec2_t(p->x, p->y);
    if(transform) last = last.transform(transform);
    last *= (1 << aa);
    last -= offset;

    for(int i = 0; i < path->point_count; i++) {
      p = &path->points[i];
      vec2_t next = vec2_t(p->x, p->y);
      if(transform) next = next.transform(transform);
      next *= (1 << aa);
      next -= offset;

      //printf("   - add line segment %d, %d -> %d, %d\n", int(last.x), int(last.y), int(next.x), int(next.y));
      add_line_segment_to_nodes(last, next, tb);
      last = next;
    }
  }

  void render_glyph(glyph_t *glyph, image_t *target, mat3_t *transform, brush_t *brush) {

    if(!glyph->path_count) return;

    // antialias level of target image
    uint aa = (uint)target->antialias();


    uint8_t *p_alpha_map = alpha_map_none;
    if(aa == 1) p_alpha_map = alpha_map_x4;
    if(aa == 2) p_alpha_map = alpha_map_x16;

    //printf("render shape\n");

    // determine bounds of shape to be rendered
    rect_t sb = glyph->bounds(transform).round();

    rect_t clip = target->clip();

    masked_span_func_t fn = target->_masked_span_func;

    //printf("- shape bounds %d, %d (%d x %d)\n", sbx, sby, sbw, sbh);
    //printf("- clip bounds %d, %d (%d x %d)\n", int(clip.x), int(clip.y), int(clip.w), int(clip.h));

    // iterate over tiles
    //printf("> processing tiles\n");
    for(int y = sb.y; y < sb.y + sb.h; y += TILE_HEIGHT) {
      for(int x = sb.x; x < sb.x + sb.w; x += TILE_WIDTH) {
        //printf(" > tile %d x %d\n", x, y);
        rect_t tb = rect_t(x, y, TILE_WIDTH, TILE_HEIGHT);

        //printf("  - tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));

        tb = clip.intersection(tb).intersection(sb).round();
        if(tb.empty()) { continue; } // if tile empty, skip it

        //printf("  - clipped tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));
        // screen coordinates for clipped tile
        int sx = tb.x;
        int sy = tb.y;
        int sw = tb.w;
        int sh = tb.h;

        tb.x *= (1 << aa);
        tb.y *= (1 << aa);
        tb.w *= (1 << aa);
        tb.h *= (1 << aa);

        //printf("  - clipped and scaled tile bounds %d, %d (%d x %d)\n", int(tb.x), int(tb.y), int(tb.w), int(tb.h));

        // clear existing tile data and nodes
        memset(node_count_buffer, 0, NODE_COUNT_BUFFER_SIZE);
        for (int row = 0; row <= sh; ++row) {
          memset(&tile_buffer[row * TILE_WIDTH], 0, sw);
        }

        //memset(tile_buffer, 0, TILE_WIDTH * TILE_HEIGHT);

        // build the nodes for each path
        for(int i = 0; i < glyph->path_count; i++) {
          glyph_path_t *p = &glyph->paths[i];
          build_glyph_nodes(p, &tb, transform, aa);
        }

        rect_t rb = render_nodes(&tb, aa).round();

        if(tb.empty()) { continue; }

        int rbx = rb.x;
        int rby = rb.y;
        int rbw = rb.w;
        int rbh = rb.h;

        for(int ty = rby; ty < rby + rbh; ty++) {
          uint8_t* p;

          // scale tile buffer values to alpha values
          p = &tile_buffer[ty * TILE_WIDTH + rbx];
          int c = rbw;
          while(c--) {
            *p = p_alpha_map[*p];
            p++;
          }

          // render tile span
          p = &tile_buffer[ty * TILE_WIDTH + rbx];
          fn(target, brush, sx + rbx, sy + ty, rbw, p);
        }
      }
    }
  }
}
